import json
import copy
import sys
import inspect

from versionedobj.exceptions import InvalidVersionAttributeError, InputValidationError
from versionedobj.utils import _ObjField, _iter_obj_attrs, _walk_obj_attrs, _obj_to_dict


def add_migration(migration_func, cls, from_version, to_version):
    """
    Add a migration function to an object class. Use this function to register a
    migration function that should be used for migrating an object from one version
    to another. This is an equivalent alternative to the versionedobj.objbect.migration
    decorator.

    :param callable migration_func: Function to call to perform the migration
    :param cls: Class object to add migration to
    :param from_version: Version to migrate from. If you are migrating an object that\
        previously had no version number, use 'None' here.
    :param to_version: Version to migrate to
    """
    try:
        version = cls.__dict__['version']
    except KeyError:
        raise ValueError("Cannot add migration to un-versioned object. Add a 'version' attribute.")

    cls._vobj__migrations.append((from_version, to_version, migration_func))


def migration(cls, from_version, to_version):
    """
    Decorator for adding a migration function to an object class. Use this
    decorator on any function or method that should be used for migrating an
    object from one version to another. This is an equivalent alternative to the
    versionedobject.object.add_migration function.

    :param cls: Class object to add migration to
    :param from_version: Version to migrate from. If you are migrating an object that\
        previously had no version number, use 'None' here.
    :param to_version: Version to migrate to
    """
    def _inner_migration(migration_func):
        add_migration(migration_func, cls, from_version, to_version)

    return _inner_migration


class MigrationResult(object):
    """
    Value returned by Serializer.from_dict, Serializer.from_file, and Serializer.from_json methods,
    if a successful or partial object migration was performed.

    :ivar old_version: the object version before migration was attempted
    :ivar target_version: the target version of the migration (current version)
    :ivar version_reached: the actual object version after migration (this should\
        match target_version after a successful migration)
    :ivar bool success: True if migration was successful, false otherwise
    """
    def __init__(self, old_version, target_version, version_reached, success):
        self.old_version = old_version
        self.target_version = target_version
        self.version_reached = version_reached
        self.success = success


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
    def __new__(cls, name, bases, dic):
        dic['_vobj__migrations'] = []
        return super().__new__(cls, name, bases, dic)


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
        self._vobj__field_count = 0
        self._vobj__populate_instance()

        # Set alternate initial values, if any
        if initial_values:
            for field in _walk_obj_attrs(self):
                dotname = field.dot_name()
                if dotname in initial_values:
                    field.value = initial_values[dotname]
                    field.set_obj_field(self)

    def __contains__(self, item):
        for field in _walk_obj_attrs(self):
            if field.get_obj_field(self) == item:
                return True

        return False

    def __str__(self):
        json_str = json.dumps(_obj_to_dict(self))
        if len(json_str) > 36:
            json_str = json_str[:30] + ' ... }'

        return f"{self.__class__.__name__}({json_str})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        seen_in_other = {}
        for field in _walk_obj_attrs(self):
            seen_in_other[field.dot_name()] = False

        for field in _walk_obj_attrs(other):
            seen_in_other[field.dot_name()] = True
            other_val = field.get_obj_field(other)

            try:
                self_val = field.get_obj_field(self)
            except AttributeError:
                return False

            if other_val != self_val:
                return False

        for n in seen_in_other:
            if not seen_in_other[n]:
                return False

        return True

    def __neq__(self):
        return not self.__eq__()

    def __hash__(self):
        return hash(json.dumps(_obj_to_dict(self)))

    def __len__(self):
        return self._vobj__field_count

    def _vobj__populate_instance(self):
        for n in _iter_obj_attrs(self.__class__):
            val = getattr(self.__class__, n)

            vobj_class = None
            if isinstance(val, VersionedObject):
                vobj_class = val.__class__
            elif inspect.isclass(val) and issubclass(val, VersionedObject):
                vobj_class = val
            elif isinstance(val, CustomValue):
                val = copy.deepcopy(val)

            if vobj_class:
                if hasattr(val, 'version'):
                    raise InvalidVersionAttributeError(f"{vobj_class.__name__} cannot have a version attribute. "
                                                        "Only the top-level object can have a version attribute.")

                val = vobj_class()
                self._vobj__field_count += val._vobj__field_count
            else:
                self._vobj__field_count += 1

            setattr(self, n, val)

    @classmethod
    def _vobj__migrate(cls, version, attrs):
        old_version = attrs.get('version', None)
        version_before_migration = old_version
        current_version = old_version

        result = None

        if old_version != version:
            result = MigrationResult(old_version, version, None, True)

            # Attempt migrations
            for fromversion, toversion, migrate in cls._vobj__migrations:
                if fromversion == current_version:
                    attrs = migrate(attrs)

                    current_version = toversion
                    if toversion == version:
                        break

            if current_version != version:
                result.success = False

            result.version_reached = current_version

        return result, attrs

    def __getitem__(self, key):
        try:
            field = _ObjField.from_dot_name(key, self)
            val = field.get_obj_field(self)
        except AttributeError:
            msg = f"{self.__class__.__name__} object has no attribute '{key}'"
            raise KeyError(msg) from None

        return val

    def __setitem__(self, key, value):
        field = _ObjField.from_dot_name(key, self)
        field.value = value
        field.set_obj_field(self)

    def __iter__(self):
        for field in _walk_obj_attrs(self):
            yield field.dot_name()

_ObjField.set_obj_class(VersionedObject)


