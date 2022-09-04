import inspect
import json
from json.decoder import JSONDecodeError


class LoadConfigError(Exception):
    """
    Exception raised whenever saved config data cannot be loaded, either because of
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
    Metaclass for VersionedConfig, creates the 'migrations' class attribute
    """
    def __init__(cls, name, bases, dct):
        cls.migrations = []


class ConfigField(object):
    def __init__(self, parents, fieldname, value):
        self.parents = parents
        self.fieldname = fieldname
        self.value = value

    def __str__(self):
        return f"Field({self.parents}, {self.fieldname}, {self.value})"

    def __repr__(self):
        return self.__str__()

    def get_obj_field(self, parent_obj):
        obj = parent_obj

        if self.parents:
            for pname in self.parents:
                if not hasattr(obj, pname):
                    raise LoadConfigError(f"Unrecognized attribute name '{pname}'")

                obj = getattr(obj, pname)

        if not hasattr(obj, self.fieldname):
            raise LoadConfigError(f"Unrecognized attribute name '{self.fieldname}'")

        return getattr(obj, self.fieldname)

    def set_obj_field(self, parent_obj, create_nonexistent=False):
        obj = parent_obj

        if self.parents:
            for pname in self.parents:
                if not hasattr(obj, pname):
                    if create_nonexistent:
                        setattr(obj, pname, object())
                    else:
                        raise LoadConfigError(f"Unrecognized attribute name '{pname}'")

                obj = getattr(obj, pname)

        return setattr(obj, self.fieldname, self.value)

    def set_dict_field(self, parent_attrs):
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


def _walk_obj_attrs(parent_obj):
    parents = []
    obj_stack = [(None, parent_obj)]

    while obj_stack:
        fieldname, obj = obj_stack.pop(0)
        if fieldname is not None:
            parents.append(fieldname)

        for n in _iter_obj_attrs(obj):
            value = obj.__dict__[n]
            nested_config = isinstance(value, VersionedConfig)

            if nested_config or isinstance(value, CustomValue):
                obj_stack.append((n, value))
            else:
                yield ConfigField(parents, n, value)


def _walk_dict_attrs(obj, parent_attrs):
    parents = []
    attrs_stack = [(None, parent_attrs)]

    while attrs_stack:
        fieldname, attrs = attrs_stack.pop(0)
        if fieldname is not None:
            parents.append(fieldname)

        for n in attrs:
            value = attrs[n]
            field = ConfigField(parents, n, value)
            field_value = field.get_obj_field(obj)
            nested_config = isinstance(field_value, VersionedConfig)

            if (nested_config and (type(value) == dict)) or isinstance(field_value, CustomValue):
                attrs_stack.append((n, value))
            else:
                yield field


class VersionedConfig(metaclass=__Meta):
    """
    Versioned config class supporting saving/loading to/from JSON files, and
    migrating older files to the current version
    """
    def __init__(self):
        for n in _iter_obj_attrs(self.__class__):
            val = getattr(self.__class__, n)
            setattr(self, n, val)

    @classmethod
    def add_migration(cls, from_version, to_version, migration_func):
        """
        Add a function to migrate config data from an earlier version to a later version

        :param from_version: Version to migrate from
        :param to_version: Version to migrate to
        :param migration_func: Function to perform the migration. The function should\
            accept one argument, which will be the config data as a dict, and the function\
            should do whatever transformations on the dict that are required for the\
            migration, and return the transformed dict.
        """
        try:
            version = cls.__dict__['version']
        except KeyError:
            raise ValueError("Cannot add migration to un-versioned config object. Add a 'version' attribute.")

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
            raise LoadConfigError(f"Failed to migrate from version {version_before_migration} to {version}")

        return attrs

    def to_dict(self):
        """
        Convert config object to a dict, suitable for passing to the json library

        :return: config data as a dict
        :rtype: dict
        """
        ret = {}
        for field in _walk_obj_attrs(self):
            ret = field.set_dict_field(ret)

        return ret

    def from_dict(self, attrs):
        """
        Load config data from a dict

        :param dict attrs: dict containing config data
        """
        version = self.__dict__.get('version', None)
        if version is not None:
            # Config is versioned, check if migrations are needed
            if 'version' not in attrs:
                raise ValueError("Config should be versioned, but version not found in loaded data")

            attrs = self._migrate(version, attrs)

            # Migration successful or not required, delete version field
            del attrs['version']

        for field in _walk_dict_attrs(self, attrs):
            field.set_obj_field(self)

    def to_json(self, indent=None):
        """
        Generate a JSON string containing all config data

        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.

        :return: Config data as a JSON string
        :rtype: str
        """
        return json.dumps(self.to_dict(), indent=indent)

    def from_json(self, jsonstr):
        """
        Load config data from a JSON string

        :param str jsonstr: JSON string to load
        """
        try:
            d = json.loads(jsonstr)
        except JSONDecodeError:
            raise LoadConfigError("JSON decode failure")

        self.from_dict(d)

    def to_file(self, filename, indent=None):
        """
        Save config data to a JSON file

        :param str filename: Name of file to write
        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        """
        with open(filename, 'w') as fh:
            fh.write(self.to_json(indent=indent))

    def from_file(self, filename):
        """
        Load config data from a JSON file

        :param str filename: Name of file to load
        """
        with open(filename, 'r') as fh:
            self.from_json(fh.read())
