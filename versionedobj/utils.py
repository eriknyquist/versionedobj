from versionedobj.exceptions import InvalidFilterError


class _ObjField(object):
    """
    Represents a dynamic view of a single field in a versioned object. Can be used
    to access the same field in either a VersionedConfig instance, or a dict
    """

    obj_class = None

    def __init__(self, parents, fieldname, value):
        self.parents = parents
        self.fieldname = fieldname
        self.value = value

    @classmethod
    def set_obj_class(cls, obj_class):
        cls.obj_class = obj_class

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
    """
    Generator that iterates over all attributes in obj's __dict__, skipping over anything
    that starts with "__" or with "_vobj__"
    """
    for n in obj.__dict__:
        if n.startswith('__') or n.startswith('_vobj__'):
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
    obj_stack = [(None, [], parent_obj)]

    while obj_stack:
        fieldname, parents, obj = obj_stack.pop(0)

        for n in _iter_obj_attrs(obj):
            p = parents if fieldname is None else parents + [fieldname]
            value = obj.__dict__[n]
            field = _ObjField(p, n, value)

            if isinstance(value, _ObjField.obj_class):
                obj_stack.append((n, p, value))
            else:
                if not _field_should_be_skipped(field.dot_name(), only, ignore):
                    yield field


def _obj_to_dict(obj, only=[], ignore=[]):
    """
    Serialize an object instance to a dict
    :param parent_obj: Versioned object to convert to dict
    :param list only: List of 'only' names
    :param list ignore: List of 'ignore' names
    """
    if only and ignore:
        raise InvalidFilterError("Cannot use both 'only' and 'ignore'")

    ret = {}
    for field in _walk_obj_attrs(obj, only, ignore):
        if hasattr(field.value, 'to_dict'):
            field.value = field.value.to_dict()

        ret = field.set_dict_field(ret)

    return ret
