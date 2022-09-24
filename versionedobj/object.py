import sys
import inspect
import json
from json.decoder import JSONDecodeError

from versionedobj.exceptions import InvalidFilterError, LoadObjectError, ObjectMigrationError, InputValidationError, InvalidVersionAttributeError


def migration(cls, from_version, to_version):
    """
    Decorator for migration functions. Use this decorator on any function or method
    that should be used for migrating an object from one version to another.

    :param cls: Class object to add migration to
    :param from_version: Version to migrate from. If you are migrating an object that\
        previously had no version number, use 'None' here.
    :param to_version: Version to migrate to
    """
    def _inner_migration(migration_classfunc):
        cls.add_migration(from_version, to_version, migration_classfunc)

    return _inner_migration


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

    @classmethod
    def from_dot_name(cls, dotname, parent_obj):
        parents = []
        fieldname = ""

        fields = dotname.split('.')
        if len(fields) == 0:
            raise InputValidationError("Invalid dotname")
        elif len(fields) == 1:
            fieldname = fields[0]
        else:
            fieldname = fields[-1]
            parents = fields[:-1]

        ret = _ObjField(parents, fieldname, None)
        ret.value = ret.get_obj_field(parent_obj)
        return ret

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
                obj = getattr(obj, pname)

        return getattr(obj, self.fieldname)

    def set_obj_field(self, parent_obj):
        """
        Set the field value on the provided VersionedObject instance

        :param parent_obj: object instance to set field on
        """
        obj = parent_obj

        if self.parents:
            for pname in self.parents:

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
    def __init__(self, initial_values={}):
        """
        :param dict: map of initial values. Keys are the field name, and values are\
            the initial values to set.
        """
        # Set all class attributes as instance attributes
        for n in _iter_obj_attrs(self.__class__):
            val = getattr(self.__class__, n)

            vobj_class = None
            if isinstance(val, VersionedObject):
                vobj_class = val.__class__
            elif inspect.isclass(val) and issubclass(val, VersionedObject):
                vobj_class = val

            if vobj_class:
                if hasattr(val, 'version'):
                    raise InvalidVersionAttributeError(f"{vobj_class.__name__} cannot have a version attribute. "
                                                        "Only the top-level object can have a version attribute.")

                val = vobj_class()

            setattr(self, n, val)

        # Set alternate initial values, if any
        if initial_values:
            for field in _walk_obj_attrs(self):
                dotname = field.dot_name()
                if dotname in initial_values:
                    field.value = initial_values[dotname]
                    field.set_obj_field(self)

    @classmethod
    def new_from_dict(cls, attrs, validate=True, only=[], ignore=[]):
        """
        Create a new object instance, populate it with object data from a dict, and
        return the new object instance

        :param dict attrs: dict containing object data
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        return cls().from_dict(attrs, validate, only, ignore)

    @classmethod
    def new_from_json(cls, jsonstr, validate=True, only=[], ignore=[]):
        """
        Create a new object instance, populate it with object data from a JSON string, and
        return the new object instance

        :param dict jsonstr: JSON string containing object data
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        return cls().from_json(jsonstr, validate, only, ignore)

    @classmethod
    def new_from_file(cls, filename, validate=True, only=[], ignore=[]):
        """
        Create a new object instance, populate it with object data from a JSON file, and
        return the new object instance

        :param dict filename: name of JSON file containing object data
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        return cls().from_file(filename, validate, only, ignore)

    @classmethod
    def add_migration(cls, from_version, to_version, migration_func):
        """
        Add a function to migrate object data from an earlier version to a later version

        :param from_version: Version to migrate from. If you are migrating an object that\
            previously had no version number, use 'None' here.
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
        old_version = attrs.get('version', None)
        version_before_migration = old_version
        version_after_migration = old_version

        if old_version != version:
            # Attempt migrations
            for fromversion, toversion, migrate in cls.migrations:
                if fromversion == version_after_migration:
                    attrs = migrate(attrs)

                version_after_migration = toversion
                if toversion == version:
                    break

        if version_after_migration != version:
            raise ObjectMigrationError(f"Failed to migrate from version {version_before_migration} to {version}")

        return attrs

    def __getitem__(self, key):
        field = _ObjField.from_dot_name(key, self)
        return field.get_obj_field(self)

    def __setitem__(self, key, value):
        field = _ObjField.from_dot_name(key, self)
        field.value = value
        field.set_obj_field(self)

    def object_attributes(self, only=[], ignore=[]):
        """
        Returns a generator that generates all attribute names and values.
        Can be used to iterate over all object attributes.

        :param list only: Whitelist of field names to generate (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :return: generator for all attributes
        :rtype: Iterator[tuple(attribute_name, attribute_value)]

        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        for field in _walk_obj_attrs(self, only, ignore):
            yield (field.dot_name(), field.get_obj_field(self))

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

    def validate_dict(self, attrs, only=[], ignore=[]):
        """
        Validate a versioned object in dict form.

        :param dict attrs: dict to validate
        :param list only: Whitelist of attribute names to validate (cannot be used with 'ignore')
        :param list ignore: Blacklist of attribute names to exclude from validation (cannot be used with 'only')

        :raises versionedobj.exceptions.InputValidationError: if the dict contains\
            fields that are not found in this object, or if the dict is missing\
            fields that are found in this object.

        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        # Create a map of all object attribute names, to track which attributes have
        # also been seen in the dict
        obj_attrs_loaded = {}
        for field in _walk_obj_attrs(self, only, ignore):
            dotname = field.dot_name()
            if 'version' == dotname:
                continue

            obj_attrs_loaded[dotname] = False

        # Now, walk through all attributes in the dict
        try:
            for field in _walk_dict_attrs(self, attrs, only, ignore):
                dotname = field.dot_name()

                if 'version' == dotname:
                    continue

                if dotname not in obj_attrs_loaded:
                    raise InputValidationError(f"Unrecognized attribute name '{dotname}' in dict")

                obj_attrs_loaded[dotname] = True
        except AttributeError as e:
            raise InputValidationError(str(e))

        # See if any fields were missing from the dict
        missing = []
        for n in obj_attrs_loaded:
            if not obj_attrs_loaded[n]:
                missing.append(n)

        if missing:
            raise InputValidationError(f"Attributes missing from dict: {','.join(missing)}")

    def from_dict(self, attrs, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of this object with object data from a dict.

        :param dict attrs: dict containing object data
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        version = self.__dict__.get('version', None)
        attrs = self._migrate(version, attrs)

        if validate:
            self.validate_dict(attrs, only, ignore)

        # Delete version field from dict, if it exists
        if 'version' in attrs:
            del attrs['version']

        for field in _walk_dict_attrs(self, attrs, only, ignore):
            val = field.get_obj_field(self)
            if isinstance(val, CustomValue):
                val.from_dict(field.value)
            else:
                field.set_obj_field(self)

        return self

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

    def from_json(self, jsonstr, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of this object with object data from a JSON string.

        :param str jsonstr: JSON string to load
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.LoadObjectError: if JSON parsing fails
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        try:
            d = json.loads(jsonstr)
        except JSONDecodeError:
            raise LoadObjectError("JSON decode failure")

        self.from_dict(d, validate, only, ignore)
        return self

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

    def from_file(self, filename, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of this object with object data from a JSON file.

        :param str filename: Name of file to load
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.LoadObjectError: if JSON parsing fails
        :raises versionedobj.exceptions.ObjectMigrationError: if migration to current version fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.
        """
        with open(filename, 'r') as fh:
            self.from_json(fh.read(), validate, only, ignore)

        return self
