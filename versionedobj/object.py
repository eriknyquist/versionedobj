import inspect
import json
from json.decoder import JSONDecodeError


class InvalidFilterError(Exception):
    """
    Exception raised whenever 'only' and 'ignore' filters are used at the same time
    """
    pass


class LoadObjError(Exception):
    """
    Exception raised whenever saved object data cannot be loaded, either because of
    a JSON parser error, or because of unrecognized/invalid fields
    """
    pass


class CustomValue(object):
    """
    Abstract class that can be sub-classed if you want to serialize/deserialize
    a custom class that the standard JSON parser is not handling the way you want
    """
    def to_dict(self):
        """
        Convert this object instance to something that is suitable for json.dump

        :return: object instance data as a dict, or a single value
        :rtype: any object
        """
        raise NotImplementedError()

    def from_dict(self, attrs):
        """
        Load this object instance with values from a dict returned by json.load

        :param dict attrs: object instance data
        """
        raise NotImplementedError()


class __Meta(type):
    """
    Metaclass for VersionedObject, creates the 'migrations' class attribute
    """
    def __init__(cls, name, bases, dct):
        cls.migrations = []


class _ObjField(object):
    """
    Represents a dynamic view of a single field in a versioned object. Can be used
    to access the same field in either a VersionedConfig instance, or a dict
    """
    def __init__(self, parents, fieldname, value):
        self.parents = parents
        self.fieldname = fieldname
        self.value = value

    def __str__(self):
        return f"Field({self.parents}, {self.fieldname}, {self.value})"

    def __repr__(self):
        return self.__str__()

    def dot_name(self):
        """
        Get the full object name, with sub-object names separated by dots
        """
        return '.'.join(self.parents + [self.fieldname])

    def get_obj_field(self, parent_obj):
        """
        Read the field value from the provided VersionedObject instance

        :param parent_obj: object instance to read field from

        :return: field value from object instance
        """
        obj = parent_obj

        if self.parents:
            for pname in self.parents:
                if not hasattr(obj, pname):
                    raise LoadObjError(f"Unrecognized attribute name '{pname}'")

                obj = getattr(obj, pname)

        if not hasattr(obj, self.fieldname):
            raise LoadObjError(f"Unrecognized attribute name '{self.fieldname}'")

        return getattr(obj, self.fieldname)

    def set_obj_field(self, parent_obj, create_nonexistent=False):
        """
        Set the field value on the provided VersionedObject instance

        :param parent_obj: object instance to set field on
        """
        obj = parent_obj

        if self.parents:
            for pname in self.parents:
                if not hasattr(obj, pname):
                    if create_nonexistent:
                        setattr(obj, pname, object())
                    else:
                        raise LoadObjError(f"Unrecognized attribute name '{pname}'")

                obj = getattr(obj, pname)

        return setattr(obj, self.fieldname, self.value)

    def set_dict_field(self, parent_attrs):
        """
        Set the field on the provided dict

        :param parent_attrs: dict to set field on
        """
        attrs = parent_attrs

        if self.parents:
            for pname in self.parents:
                if pname not in attrs:
                    attrs[pname] = {}

                attrs = attrs[pname]

        attrs[self.fieldname] = self.value
        return parent_attrs


def _iter_obj_attrs(obj):
    for n in obj.__dict__:
        if n.startswith('__'):
            continue

        if n == 'migrations':
            continue

        yield n

def _field_should_be_skipped(dotname, only, ignore):
    """
    Check if a field should be skipped based on 'only' and 'ignore' parameters

    :param list only: List of 'only' names
    :param list ignore: List of 'ignore' names
    """
    if only:
        found = False
        for n in only:
            if dotname.startswith(n):
                found = True
                break

        return not found

    for n in ignore:
        if dotname.startswith(n):
            return True

def _walk_obj_attrs(parent_obj, only=[], ignore=[]):
    """
    Walk all fields (including nested fields) in a versioned object, and
    generate an _ObjField instance for each field

    :param parent_obj: Versioned object to walk
    :param list only: List of 'only' names
    :param list ignore: List of 'ignore' names
    """
    parents = []
    obj_stack = [(None, parent_obj)]

    while obj_stack:
        fieldname, obj = obj_stack.pop(0)
        if fieldname is not None:
            parents.append(fieldname)

        for n in _iter_obj_attrs(obj):
            value = obj.__dict__[n]
            field = _ObjField(parents, n, value)
            dotname = field.dot_name()

            if isinstance(value, VersionedObject):
                obj_stack.append((n, value))
            else:
                if not _field_should_be_skipped(dotname, only, ignore):
                    yield field


def _walk_dict_attrs(obj, parent_attrs, only=[], ignore=[]):
    """
    Walk all fields (including nested fields) in a versioned object as a dict, and
    generate an _ObjField instance for each field

    :param parent_attrs: Dict to walk
    :param list only: List of 'only' names
    :param list ignore: List of 'ignore' names
    """
    parents = []
    attrs_stack = [(None, parent_attrs)]

    while attrs_stack:
        fieldname, attrs = attrs_stack.pop(0)
        if fieldname is not None:
            parents.append(fieldname)

        for n in attrs:
            value = attrs[n]
            field = _ObjField(parents, n, value)
            dotname = field.dot_name()
            field_value = field.get_obj_field(obj)

            if (isinstance(field_value, VersionedObject) and (type(value) == dict)):
                attrs_stack.append((n, value))
            else:
                if not _field_should_be_skipped(dotname, only, ignore):
                    yield field


class VersionedObject(metaclass=__Meta):
    """
    Versioned object class supporting saving/loading to/from JSON files, and
    migrating older files to the current version
    """
    def __init__(self):
        for n in _iter_obj_attrs(self.__class__):
            val = getattr(self.__class__, n)
            setattr(self, n, val)

    @classmethod
    def add_migration(cls, from_version, to_version, migration_func):
        """
        Add a function to migrate object data from an earlier version to a later version

        :param from_version: Version to migrate from
        :param to_version: Version to migrate to
        :param migration_func: Function to perform the migration. The function should\
            accept one argument, which will be the object data as a dict, and the function\
            should do whatever transformations on the dict that are required for the\
            migration, and then return the transformed dict.
        """
        try:
            version = cls.__dict__['version']
        except KeyError:
            raise ValueError("Cannot add migration to un-versioned object. Add a 'version' attribute.")

        cls.migrations.append((from_version, to_version, migration_func))

    @classmethod
    def _migrate(cls, version, attrs):
        version_before_migration = attrs['version']
        version_after_migration = attrs['version']

        if attrs['version'] != version:
            # Attempt migrations
            for fromversion, toversion, migrate in cls.migrations:
                if fromversion == version_after_migration:
                    attrs = migrate(attrs)

                version_after_migration = toversion
                if toversion == version:
                    break

        if version_after_migration != version:
            raise LoadObjError(f"Failed to migrate from version {version_before_migration} to {version}")

        return attrs

    def to_dict(self, only=[], ignore=[]):
        """
        Convert object to a dict, suitable for passing to the json library

        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :return: object data as a dict
        :rtype: dict
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        ret = {}
        for field in _walk_obj_attrs(self, only, ignore):
            if isinstance(field.value, CustomValue):
                field.value = field.value.to_dict()

            ret = field.set_dict_field(ret)

        return ret

    def from_dict(self, attrs, only=[], ignore=[]):
        """
        Load object data from a dict

        :param dict attrs: dict containing object data
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        version = self.__dict__.get('version', None)
        if version is not None:
            # Object is versioned, check if migrations are needed
            if 'version' not in attrs:
                raise ValueError("Object should be versioned, but version not found in loaded data")

            attrs = self._migrate(version, attrs)

            # Migration successful or not required, delete version field
            del attrs['version']

        for field in _walk_dict_attrs(self, attrs, only, ignore):
            val = field.get_obj_field(self)
            if isinstance(val, CustomValue):
                val.from_dict(field.value)
            else:
                field.set_obj_field(self)

    def to_json(self, indent=None, only=[], ignore=[]):
        """
        Generate a JSON string containing all object data

        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :return: Object data as a JSON string
        :rtype: str
        """
        return json.dumps(self.to_dict(only, ignore), indent=indent)

    def from_json(self, jsonstr, only=[], ignore=[]):
        """
        Load object data from a JSON string

        :param str jsonstr: JSON string to load
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)
        """
        try:
            d = json.loads(jsonstr)
        except JSONDecodeError:
            raise LoadObjError("JSON decode failure")

        self.from_dict(d, only, ignore)

    def to_file(self, filename, indent=None, only=[], ignore=[]):
        """
        Save object data to a JSON file

        :param str filename: Name of file to write
        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)
        """
        with open(filename, 'w') as fh:
            fh.write(self.to_json(indent, only, ignore))

    def from_file(self, filename, only=[], ignore=[]):
        """
        Load object data from a JSON file

        :param str filename: Name of file to load
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)
        """
        with open(filename, 'r') as fh:
            self.from_json(fh.read(), only, ignore)
