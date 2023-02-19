import inspect

from versionedobj.object import CustomValue, VersionedObject
from versionedobj.serializer import Serializer


class ListField(CustomValue):
    """
    List class that allows putting a sequence of VersionedObject instances in a
    single VersionedObject field. Behaves like a regular python list, except that it
    can only contain VersionedObject instances, and can only contain instances of
    the same VersionedObject class.
    """
    def __init__(self, arg):
        self._obj_class = None
        self._values = []

        if inspect.isclass(arg) and issubclass(arg, VersionedObject):
            # Arg is the object class for this list
            self._obj_class = arg
        else:
            # Arg is an interable of instance values
            iterable = True
            try:
                _ = [i for i in arg]
            except TypeError:
                iterable = False

            if iterable:
                for i in arg:
                    if not isinstance(i, VersionedObject):
                        raise ValueError("ListField may only contain VersionedObject instances")

                    if self._obj_class is None:
                        self._obj_class = i.__class__
                    else:
                        if self._obj_class != i.__class__:
                            raise ValueError("ListField may only contain objects of the same class")

                    self._values.append(i)

        if self._obj_class is None:
            raise ValueError("Invalid argument, provide a VersionedObject class or a list of VersionedObject instances")

        self._serializer = Serializer(self._obj_class)

    def _check_value(self, v):
        if not isinstance(v, self._obj_class):
            raise ValueError(f"Only instances of the {self._obj_class.__name__} class can be added to this list")

    def _check_index(self, i):
        if i >= len(self._values):
            raise IndexError("List index out of bounds")

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, i):
        self._check_index(i)
        return self._values[i]

    def __setitem__(self, i, v):
        self._check_index(i)
        self._check_value(v)
        self._values[i] = v

    def __delitem__(self, i):
        self._check_index(i)
        del self._values[i]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return (i for i in self._values)

    def __add__(self, other):
        if isinstance(other, ListField):
            othervals = other._values
        else:
            othervals = other

        return ListField(self._values + list(othervals))

    def __iadd__(self, other):
        if isinstance(other, ListField):
            othervals = other._values
        else:
            othervals = other

        self._values += list(othervals)
        return self

    def __eq__(self, other):
        if isinstance(other, ListField):
            othervals = other._values
        else:
            othervals = other

        return list(self._values) == list(othervals)

    def append(self, v):
        """
        Append a value to the list

        :param versionedobj.VersionedObject v: value to append
        :raises ValueError: if v is not an instance of a VersionedObject
        """
        self._check_value(v)
        self._values.append(v)

    def insert(self, i, v):
        """
        Insert a value at a specific position in the list

        :param int i: list position to insert new item at
        :param versionedobj.VersionedObject v: value to insert
        :raises ValueError: if v is not an instance of a VersionedObject
        :raises IndexError: if i is not a valid index in the list
        """
        self._check_index(i)
        self._check_value(v)
        self._values.insert(i, v)

    def to_dict(self):
        """
        Convert the list to JSON-serializable dict

        :return: serialized dict
        """
        return [self._serializer.to_dict(i) for i in self._values]

    def from_dict(self, attrs):
        """
        Populate the list with data from a dict
        """
        self._values = []
        for d in attrs:
            ins = self._obj_class()
            self._serializer.from_dict(d, ins)
            self._values.append(ins)
