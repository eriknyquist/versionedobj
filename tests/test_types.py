import os
from unittest import TestCase

from versionedobj import types, VersionedObject


class Val(VersionedObject):
    val = 0

    def __init__(self, val=0):
        super(Val, self).__init__(initial_values={"val": val})

class WrongVal(VersionedObject):
    val = 0

    def __init__(self, val=0):
        super(WrongVal, self).__init__(initial_values={"val": val})


class TestTypes(TestCase):
    def test_exceptions(self):
        """
        Tests that types.ListField throws all the expected exceptions
        """
        # init errors
        self.assertRaises(ValueError, types.ListField, 5)
        self.assertRaises(ValueError, types.ListField, "hdth")
        self.assertRaises(ValueError, types.ListField, True)
        self.assertRaises(ValueError, types.ListField, 44.4)
        self.assertRaises(ValueError, types.ListField, [44.4])
        self.assertRaises(ValueError, types.ListField, [Val(1), 44.4])
        self.assertRaises(ValueError, types.ListField, [])
        self.assertRaises(ValueError, types.ListField, [Val(1), WrongVal(1)])

        # append errors
        x = types.ListField([Val(1), Val(2)])
        self.assertRaises(ValueError, x.append, WrongVal(1))

        # insert errors
        self.assertRaises(ValueError, x.insert, 0, WrongVal(1))
        self.assertRaises(IndexError, x.insert, 99, Val(1))

        # index read error
        read_exception = False
        try:
            _ = x[99]
        except IndexError:
            read_exception = True
        self.assertTrue(read_exception)

        # index write error
        write_exception = False
        try:
            x[99] = Val(1)
        except IndexError:
            write_exception = True
        self.assertTrue(write_exception)

        # delete index error
        del_exception = False
        try:
            del x[99]
        except IndexError:
            del_exception = True
        self.assertTrue(del_exception)

    def test_list_basic(self):
        """
        Tests that types.ListField behaves like a list for basic/common operations
        """
        source_data = [Val(1), Val(2), Val(3), Val(4)]
        x = types.ListField(source_data)

        # List equality
        self.assertEqual(x, source_data)
        self.assertEqual(x, types.ListField(source_data))

        # List length
        self.assertEqual(len(x), len(source_data))

        # Reading by index
        self.assertEqual(x[2], source_data[2])

        # Setting by index
        x[2] = Val(333)
        self.assertEqual(x[2], Val(333))
        self.assertEqual(x, [Val(1), Val(2), Val(333), Val(4)])

        # Appending
        x.append(Val(5))
        self.assertEqual(x, [Val(1), Val(2), Val(333), Val(4), Val(5)])
        self.assertEqual(len(x), len(source_data) + 1)
        x.append(Val(66))
        self.assertEqual(x, [Val(1), Val(2), Val(333), Val(4), Val(5), Val(66)])
        self.assertEqual(len(x), len(source_data) + 2)

        # Inserting
        x.insert(0, Val(None))
        self.assertEqual(x, [Val(None), Val(1), Val(2), Val(333), Val(4), Val(5), Val(66)])
        self.assertEqual(len(x), len(source_data) + 3)
        x.insert(3, Val("!"))
        self.assertEqual(x, [Val(None), Val(1), Val(2), Val("!"), Val(333), Val(4), Val(5), Val(66)])
        self.assertEqual(len(x), len(source_data) + 4)

    def test_list_iteration(self):
        """
        Tests that types.ListField behaves like a list for iteration stuff
        """
        source_data = [Val(1), Val(2), Val(3), Val(4), Val(True), Val(33.3), Val(1212123)]
        x = types.ListField(source_data)

        # Iteration
        count = 0
        for value in x:
            self.assertEqual(x[count], source_data[count])
            count += 1

        for i in range(len(x)):
            self.assertEqual(x[i], source_data[i])

    def test_list_combining(self):
        """
        Tests that types.ListField behaves like a list when adding lists together
        """
        x = types.ListField([Val(5), Val(6), Val(7)])

        # test __iadd__
        x += [Val(8), Val(9)]
        self.assertEqual(x, [Val(5), Val(6), Val(7), Val(8), Val(9)])
        x += types.ListField([Val(10), Val(11)])
        self.assertEqual(x, [Val(5), Val(6), Val(7), Val(8), Val(9), Val(10), Val(11)])

        # test __add__
        x1 = x + [Val(12), Val(13)]
        self.assertEqual(x1, [Val(5), Val(6), Val(7), Val(8), Val(9), Val(10), Val(11), Val(12), Val(13)])

        x2 = x1 + types.ListField([Val(14), Val(15)])
        self.assertEqual(x2, [Val(5), Val(6), Val(7), Val(8), Val(9), Val(10), Val(11), Val(12), Val(13),
                              Val(14), Val(15)])

    def test_list_to_from_dict(self):
        """
        Tests that types.ListField behaves as expected when serialized to and from a dict
        """

        test_data = [
            ([Val(1), Val(2), Val(3)], [{'val': 1}, {'val': 2}, {'val': 3}]),
            ([Val("abc"), Val("def"), Val("ghi")], [{'val': "abc"}, {'val': "def"}, {'val': "ghi"}]),
            ([Val(True), Val(False)], [{'val': True}, {'val': False}]),
            ([Val(1), Val("qqq"), Val(38.6)], [{'val': 1}, {'val': "qqq"}, {'val': 38.6}]),
        ]

        for input_list, expected_dict in test_data:
            L = types.ListField(input_list)
            L2 = types.ListField(Val)
            L2.from_dict(expected_dict)

            self.assertEqual(L.to_dict(), expected_dict)
            self.assertEqual(L, L2)
