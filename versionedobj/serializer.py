import os
import inspect
import json
from json.decoder import JSONDecodeError

from versionedobj.object import VersionedObject, CustomValue
from versionedobj.utils import _ObjField, _walk_obj_attrs, _field_should_be_skipped, _obj_to_dict
from versionedobj.exceptions import InvalidFilterError, LoadObjectError, InputValidationError, InvalidVersionAttributeError


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


class Serializer(object):
    """
    Class for serializing/deserializing any VersionedObject types
    """
    def __init__(self):
        pass

    def to_dict(self, obj, only=[], ignore=[]):
        """
        Convert object to a dict, suitable for passing to the json library

        :param obj: VersionedObject instance to convert
        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :return: object data as a dict
        :rtype: dict
        """
        return _obj_to_dict(obj, only, ignore)

    def validate_dict(self, obj, attrs, only=[], ignore=[]):
        """
        Validate a versioned object in dict form.

        :param obj: VersionedObject instance you want to validate the dict against
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
        for field in _walk_obj_attrs(obj, only, ignore):
            dotname = field.dot_name()
            if 'version' == dotname:
                continue

            obj_attrs_loaded[dotname] = False

        # Now, walk through all attributes in the dict
        try:
            for field in _walk_dict_attrs(obj, attrs, only, ignore):
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

    def from_dict(self, obj, attrs, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of a VersionedObjbect instance, with object data from a dict.

        :param obj: VersionedObject instance to populate
        :param dict attrs: dict containing object data
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.

        :return: MigrationResult object describing the object migration that was peformed, or\
            None if no object migrations were required
        :rtype: MigrationResult
        """
        if only and ignore:
            raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

        version = obj.__dict__.get('version', None)
        migration_result, attrs = obj._vobj__migrate(version, attrs)
        if (migration_result is not None) and (not migration_result.success):
            return migration_result

        if validate:
            self.validate_dict(obj, attrs, only, ignore)

        # Delete version field from dict, if it exists
        if 'version' in attrs:
            del attrs['version']

        for field in _walk_dict_attrs(obj, attrs, only, ignore):
            val = field.get_obj_field(obj)
            if isinstance(val, CustomValue):
                val.from_dict(field.value)
            else:
                field.set_obj_field(obj)

        return migration_result

    def to_json(self, obj, indent=None, only=[], ignore=[]):
        """
        Generate a JSON string containing all data from a VersionedObject instance

        :param obj: VersionedObject instance
        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :return: Object data as a JSON string
        :rtype: str
        """
        return json.dumps(self.to_dict(obj, only, ignore), indent=indent)

    def from_json(self, obj, jsonstr, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of a VersionedObject instance with object data from a JSON string.

        :param obj: VersionedObject instance to populate
        :param str jsonstr: JSON string to load
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.LoadObjectError: if JSON parsing fails
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.

        :return: MigrationResult object describing the object migration that was peformed, or\
            None if no object migrations were required
        :rtype: MigrationResult
        """
        try:
            d = json.loads(jsonstr)
        except JSONDecodeError:
            raise LoadObjectError("JSON decode failure")

        return self.from_dict(obj, d, validate, only, ignore)

    def to_file(self, obj, filename, indent=None, only=[], ignore=[]):
        """
        Save VersionedObject instance data to a JSON file

        :param obj: VersionedObject instance
        :param str filename: Name of file to write
        :param int indent: Indentation level to use, in columns. If None, everything will be on one line.
        :param list only: Whitelist of field names to serialize (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)
        """
        with open(filename, 'w') as fh:
            fh.write(self.to_json(obj, indent, only, ignore))

    def from_file(self, obj, filename, validate=True, only=[], ignore=[]):
        """
        Populate instance attributes of a VersionedObject instance with object data from a JSON file.

        :param obj: VersionedObject instance to populate
        :param str filename: Name of file to load
        :param bool validate: If false, pre-validation will be skipped for the input data.\
            This may be useful if you want to load a partial object that is missing some fields,\
            and don't want to mess with filtering.
        :param list only: Whitelist of field names to load (cannot be used with blacklist)
        :param list ignore: Blacklist of field names to ignore (cannot be used with whitelist)

        :raises versionedobj.exceptions.InputValidationError: if validation of input data fails.
        :raises versionedobj.exceptions.LoadObjectError: if JSON parsing fails
        :raises versionedobj.exceptions.InvalidFilterError: if both 'only' and 'ignore' are provided.

        :return: MigrationResult object describing the object migration that was peformed, or\
            None if no object migrations were required
        :rtype: MigrationResult
        """
        with open(filename, 'r') as fh:
            return self.from_json(obj, fh.read(), validate, only, ignore)

    def reset_to_defaults(self, obj):
        """
        Resets instance attribute values of a VersionedObject instance back to the
        default values defined in the matching class attributes.

        :param obj: VersionedObject instance to reset
        """
        obj._vobj__populate_instance()


class FileLoader(object):
    """
    Context manager for modifying object data saved to a JSON file. Deserializes
    the object on entry, if it exists, allowing you to modify the deserialized object, and
    serializes the changed object data back to the same file on exit.
    """
    def __init__(self, instance_or_class, filename):
        if isinstance(instance_or_class, VersionedObject):
            self.obj = instance_or_class
        elif inspect.isclass(instance_or_class) and issubclass(instance_or_class, VersionedObject):
            self.obj = instance_or_class()
        else:
            raise ValueError("First argument must be a VersionedObject instance or class object")

        self.filename = filename
        self.serializer = Serializer()

    def __enter__(self):
        if os.path.isfile(self.filename):
            self.serializer.from_file(self.obj, self.filename)

        return self.obj

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.serializer.to_file(self.obj, self.filename)
