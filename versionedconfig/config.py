import inspect
import json


class __Meta(type):
    def __init__(cls, name, bases, dct):
        cls.migrations = []


class VersionedConfig(metaclass=__Meta):
    @classmethod
    def _load_attr(cls, name, value):
        attr = cls.__dict__.get(name, None)
        if inspect.isclass(attr) and issubclass(attr, VersionedConfig):
            attr.from_dict(value)
        else:
            setattr(cls, name, value)

    @classmethod
    def _migrate(cls, version, attrs):
        version_before_migration = attrs['version']
        version_after_migration = attrs['version']
        
        if attrs['version'] != version:
            # Attempt migrations
            for fromversion, toversion, migrate in cls.migrations:
                if fromversion == version:
                    attrs = migrate(attrs)

                version_after_migration = toversion
                if toversion == version:
                    break

        if version_after_migration != version:
            raise ValueError(f"Failed to migrate from version {version_before_migration} to {version}")

        return attrs

    @classmethod
    def to_dict(cls):
        """
        Convert config object to a dict, suitable for passing to the json library

        :return: config data as a dict
        :rtype: dict
        """
        ret = {}
        for n in cls.__dict__:
            if n.startswith('__'):
                continue

            if n == 'migrations':
                continue

            value = cls.__dict__[n]
            if inspect.isclass(value) and issubclass(value, VersionedConfig):
                ret[n] = value.to_dict()
            else:
                ret[n] = value

        return ret

    @classmethod
    def from_dict(cls, attrs):
        """
        Load config data from a dict

        :param dict attrs: dict containing config data
        """
        version = cls.__dict__.get('version', None)
        if version is not None:
            # Config is versioned, check if migrations are needed
            if 'version' not in attrs:
                raise ValueError("Config should be versioned, but version not found in loaded data")

            attrs = cls._migrate(version, attrs)

        for n in attrs:
            if n == 'version':
                continue

            cls._load_attr(n, attrs[n])

    @classmethod
    def to_json(self, indent=None):
        """
        Generate a JSON string containing all config data

        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.

        :return: Config data as a JSON string
        :rtype: str
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(self, jsonstr):
        """
        Load config data from a JSON string

        :param str jsonstr: JSON string to load
        """
        self.from_dict(json.loads(jsonstr))

    @classmethod
    def to_file(self, filename, indent=None):
        """
        Save config data to a JSON file

        :param str filename: Name of file to write
        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        """
        with open(filename, 'w') as fh:
            fh.write(self.to_json(indent=indent))

    @classmethod
    def from_file(self, filename):
        """
        Load config data from a JSON file

        :param str filename: Name of file to load
        """
        with open(filename, 'r') as fh:
            self.from_json(fh.read())

    @classmethod
    def add_migration(cls, from_version, to_version, migration_func):
        """
        Add a function for migration config data from an earlier version to a later version

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
