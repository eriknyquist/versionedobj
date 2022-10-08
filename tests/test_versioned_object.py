import os
from unittest import TestCase

from versionedobj import (VersionedObject, LoadObjectError, InvalidFilterError, Serializer, CustomValue, migration)


class TestVersionedObject(TestCase):
    def test_instantiation_with_initial_values(self):
        """
        Tests that the setting the 'initial_values' parameter for the VersionedObject constructor
        results in all corresponding instance attributes being set
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig(initial_values={'var1': 99, 'var2.var2': "changed"})

        self.assertEqual(99, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual("changed", cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

    def test_change_default_values_on_class_attrs_1(self):
        """
        Tests that the class attributes of a VersionedObject are used as the default
        values for created instances, and that the class attributes can be changed independently
        of the instance attributes (using instance of nested object)
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig()

        # Instance vars and class vars should match right now
        self.assertEqual(4, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

        self.assertEqual(4, TestConfig.var1)
        self.assertEqual("hello", TestConfig.var2.var1)
        self.assertEqual(55.5, TestConfig.var2.var2)
        self.assertEqual(True, TestConfig.var3)

        # Now, change some values on the instance
        cfg.var1 = 99
        cfg.var2.var1 = "changed"
        cfg.var2.var2 = 0.0
        cfg.var3 = False

        # Create a 2nd instance, values should still match original defaults
        cfg2 = TestConfig()
        self.assertEqual(4, cfg2.var1)
        self.assertEqual("hello", cfg2.var2.var1)
        self.assertEqual(55.5, cfg2.var2.var2)
        self.assertEqual(True, cfg2.var3)

        # Now change default values
        NestedConfig.var1 = "xxx"
        NestedConfig.var2 = "yyy"
        TestConfig.var1 = "zzz"
        TestConfig.var3 = "aaa"

        # Create a new instance, values should match new defaults
        cfg3 = TestConfig()
        self.assertEqual("zzz", cfg3.var1)
        self.assertEqual("xxx", cfg3.var2.var1)
        self.assertEqual("yyy", cfg3.var2.var2)
        self.assertEqual("aaa", cfg3.var3)

        # Other instance values should not have changed
        self.assertEqual(4, cfg2.var1)
        self.assertEqual("hello", cfg2.var2.var1)
        self.assertEqual(55.5, cfg2.var2.var2)
        self.assertEqual(True, cfg2.var3)

        self.assertEqual(99, cfg.var1)
        self.assertEqual("changed", cfg.var2.var1)
        self.assertEqual(0.0, cfg.var2.var2)
        self.assertEqual(False, cfg.var3)

    def test_change_default_values_on_class_attrs_2(self):
        """
        Tests that the class attributes of a VersionedObject are used as the default
        values for created instances, and that the class attributes can be changed independently
        of the instance attributes (using class object of nested object)
        """
        # Same as the previous test, except we use the NestConfig class object instead
        # of creating an instance.... behaviour should be exactly the same
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig
            var3 = True

        cfg = TestConfig()

        # Instance vars and class vars should match right now
        self.assertEqual(4, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

        self.assertEqual(4, TestConfig.var1)
        self.assertEqual("hello", TestConfig.var2.var1)
        self.assertEqual(55.5, TestConfig.var2.var2)
        self.assertEqual(True, TestConfig.var3)

        # Now, change some values on the instance
        cfg.var1 = 99
        cfg.var2.var1 = "changed"
        cfg.var2.var2 = 0.0
        cfg.var3 = False

        # Create a 2nd instance, values should still match original defaults
        cfg2 = TestConfig()
        self.assertEqual(4, cfg2.var1)
        self.assertEqual("hello", cfg2.var2.var1)
        self.assertEqual(55.5, cfg2.var2.var2)
        self.assertEqual(True, cfg2.var3)

        # Now change default values
        NestedConfig.var1 = "xxx"
        NestedConfig.var2 = "yyy"
        TestConfig.var1 = "zzz"
        TestConfig.var3 = "aaa"

        # Create a new instance, values should match new defaults
        cfg3 = TestConfig()
        self.assertEqual("zzz", cfg3.var1)
        self.assertEqual("xxx", cfg3.var2.var1)
        self.assertEqual("yyy", cfg3.var2.var2)
        self.assertEqual("aaa", cfg3.var3)

        # Other instance values should not have changed
        self.assertEqual(4, cfg2.var1)
        self.assertEqual("hello", cfg2.var2.var1)
        self.assertEqual(55.5, cfg2.var2.var2)
        self.assertEqual(True, cfg2.var3)

        self.assertEqual(99, cfg.var1)
        self.assertEqual("changed", cfg.var2.var1)
        self.assertEqual(0.0, cfg.var2.var2)
        self.assertEqual(False, cfg.var3)

    def test_access_by_dotname_1(self):
        """
        Tests that all instance attributes on a VersionedObject can be accessed by dotname
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        cfg = TestConfig()

        self.assertEqual(1, cfg['var1'])
        self.assertEqual(2, cfg['var2'])

    def test_access_by_dotname_2(self):
        """
        Tests that all instance attributes on a VersionedObject can be accessed by dotname
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = False

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        cfg = TestConfig()

        self.assertEqual(1, cfg['var1'])
        self.assertEqual("hey", cfg['var2.var1'])
        self.assertEqual(False, cfg['var2.var2'])

    def test_write_by_dotname_1(self):
        """
        Tests that all instance attributes on a VersionedObject can be written by dotname
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        cfg = TestConfig()

        cfg['var1'] = 3
        cfg['var2'] = 4

        self.assertEqual(3, cfg['var1'])
        self.assertEqual(4, cfg['var2'])

    def test_write_by_dotname_2(self):
        """
        Tests that all instance attributes on a VersionedObject can be written by dotname
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = False

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        cfg = TestConfig()

        cfg['var1'] = 99
        cfg['var2.var1'] = "xxx"
        cfg['var2.var2'] = True

        self.assertEqual(99, cfg['var1'])
        self.assertEqual("xxx", cfg['var2.var1'])
        self.assertEqual(True, cfg['var2.var2'])

    def test_iter_object_attributes_1(self):
        """
        Tests that iter_objbect_attributes provides all expected attribute names/values
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "qq"
            var3 = 77

        cfg = TestConfig()
        retrieved = {}

        for name in cfg:
            retrieved[name] = cfg[name]

        self.assertEqual(3, len(retrieved))
        self.assertEqual(1, retrieved['var1'])
        self.assertEqual("qq", retrieved['var2'])
        self.assertEqual(77, retrieved['var3'])

    def test_iter_object_attributes_2(self):
        """
        Tests that iter_objbect_attributes provides all expected attribute names/values
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = False

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        cfg = TestConfig()
        retrieved = {}

        for name in cfg:
            retrieved[name] = cfg[name]

        self.assertEqual(3, len(retrieved))
        self.assertEqual(1, retrieved['var1'])
        self.assertEqual("hey", retrieved['var2.var1'])
        self.assertEqual(False, retrieved['var2.var2'])

    def test_iter_and_set_object_attributes_1(self):
        """
        Tests that attribute values can be changed while iterating with iter_object_attributes
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 123
            var2 = 8.8
            var3 = "yy"

        cfg = TestConfig()

        for name in cfg:
            cfg[name] = 99

        self.assertEqual(99, cfg.var1)
        self.assertEqual(99, cfg.var2)
        self.assertEqual(99, cfg.var3)

    def test_iter_and_set_object_attributes_2(self):
        """
        Tests that attribute values can be changed while iterating with iter_object_attributes
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 66
            var2 = 44

        class TestConfig(VersionedObject):
            var1 = 123
            var2 = NestedConfig()

        cfg = TestConfig()

        for name in cfg:
            cfg[name] = 99

        self.assertEqual(99, cfg.var1)
        self.assertEqual(99, cfg.var2.var1)
        self.assertEqual(99, cfg.var2.var2)

    def test_nested_class_or_instance(self):
        """
        Tests that object instances are created the same whether a nested object is
        added as a class object or as an instance object
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = False

        class TestConfig1(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        class TestConfig2(VersionedObject):
            var1 = 1
            var2 = NestedConfig

        cfg1 = TestConfig1()

        NestedConfig.var1 = "xxx"

        cfg2 = TestConfig2()

        self.assertEqual(1, cfg1.var1)
        self.assertEqual("hey", cfg1.var2.var1)
        self.assertEqual(False, cfg1.var2.var2)

        self.assertEqual(1, cfg2.var1)
        self.assertEqual("xxx", cfg2.var2.var1)
        self.assertEqual(False, cfg2.var2.var2)

    def test_object_equality_success_1(self):
        """
        Tests basic successful object equality/comparison (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        self.assertTrue(cfg1 == cfg2)

    def test_object_equality_success_2(self):
        """
        Tests basic successful object equality/comparison (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 77
            var2 = 88
            var3 = 44

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig()

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        self.assertTrue(cfg1 == cfg2)

    def test_object_equality_same_attrs_diff_class_1(self):
        """
        Tests that object equality/comparison fails when two objects have identical
        attributes / values, but each object is a different class (no nested objects)
        """
        class TestConfig1(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        class TestConfig2(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig1()
        cfg2 = TestConfig2()

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_same_attrs_diff_class_2(self):
        """
        Tests that object equality/comparison fails when two objects have identical
        attributes / values, but each object is a different class (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = "qq"
            var2 = 5657

        class TestConfig1(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        class TestConfig2(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        cfg1 = TestConfig1()
        cfg2 = TestConfig2()

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_other_value_1(self):
        """
        Tests unsuccessful object equality/comparison, other object has different value
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg2.var4 = True

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_other_value_2(self):
        """
        Tests unsuccessful object equality/comparison, other object has different value
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 554
            var2 = 9348
            var3 = "fdgsdgh"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg2.var4.var2 = 3

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_self_value_1(self):
        """
        Tests unsuccessful object equality/comparison, self object has different value
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg1.var4 = True

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_self_value_2(self):
        """
        Tests unsuccessful object equality/comparison, self object has different value
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 554
            var2 = 9348
            var3 = "fdgsdgh"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg1.var4.var2 = 3

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_other_attr_1(self):
        """
        Tests unsuccessful object equality/comparison, other object has unrecognized attr
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        setattr(cfg2, 'badattr', 66)

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_other_attr_2(self):
        """
        Tests unsuccessful object equality/comparison, other object has unrecognized attr
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 554
            var2 = 9348
            var3 = "fdgsdgh"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        setattr(cfg2.var4, 'badattr', 66)

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_self_attr_1(self):
        """
        Tests unsuccessful object equality/comparison, self object has unrecognized attr
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = False

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        setattr(cfg1, 'badattr', 66)

        self.assertFalse(cfg1 == cfg2)

    def test_object_equality_fail_self_attr_2(self):
        """
        Tests unsuccessful object equality/comparison, self object has unrecognized attr
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 554
            var2 = 9348
            var3 = "fdgsdgh"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = 88.8
            var4 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        setattr(cfg1.var4, 'badattr', 66)

        self.assertFalse(cfg1 == cfg2)

    def test_object_as_dictkey_1(self):
        """
        Tests object hashing by verifying that obbject instances with different values
        can be used as unique dict keys (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = [1,2,3]

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg2.var1 = 2

        d = {}

        d[cfg1] = "a"
        d[cfg2] = "b"

        self.assertEqual(2, len(d))
        self.assertEqual("a", d[cfg1])
        self.assertEqual("b", d[cfg2])

    def test_object_as_dictkey_2(self):
        """
        Tests object hashing by verifying that obbject instances with different values
        can be used as unique dict keys (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 44.4
            var2 = "yah"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg2.var3.var2 = "y"

        d = {}

        d[cfg1] = "a"
        d[cfg2] = "b"

        self.assertEqual(2, len(d))
        self.assertEqual("a", d[cfg1])
        self.assertEqual("b", d[cfg2])

    def test_object_as_dictkey_3(self):
        """
        Test object hashing by verifying that two object instances of the same
        value overwrite each other when used as a dict key
        """
        class NestedConfig(VersionedObject):
            var1 = 44.4
            var2 = "yah"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = NestedConfig

        cfg1 = TestConfig()
        cfg2 = TestConfig()

        d = {}
        d[cfg1] = "a"
        d[cfg2] = "b"

        self.assertEqual(1, len(d))
        self.assertEqual("b", d[cfg2])

        d[cfg1] = "a"
        self.assertEqual(1, len(d))
        self.assertEqual("a", d[cfg1])

    def test_object_as_dictkey_invalid_key_1(self):
        """
        Tests that expected exception is raised when object is accessed as a dict with
        an invalid key (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = True

        cfg = TestConfig()

        raised = False
        val = None
        try:
            val = cfg['var4']
        except KeyError:
            raised = True

        self.assertTrue(raised)
        self.assertIs(None, val)

    def test_object_as_dictkey_invalid_key_2(self):
        """
        Tests that expected exception is raised when object is accessed as a dict with
        an invalid key (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 44.4
            var2 = "yah"

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "ff"
            var3 = NestedConfig

        cfg = TestConfig()

        raised = False
        val = None
        try:
            val = cfg['var3.srgrg']
        except KeyError:
            raised = True

        self.assertTrue(raised)
        self.assertIs(None, val)

    def test_contains_value_1(self):
        """
        Tests __contains__ dunder method (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = 55.5

        cfg = TestConfig()

        self.assertTrue(0 in cfg)
        self.assertTrue("ff" in cfg)
        self.assertTrue(55.5 in cfg)

        self.assertFalse(99 in cfg)
        self.assertFalse("hh" in cfg)

        cfg.var1 = 99
        self.assertTrue(99 in cfg)
        self.assertTrue("ff" in cfg)
        self.assertTrue(55.5 in cfg)

    def test_contains_value_2(self):
        """
        Tests __contains__ dunder method (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = "a"
            var2 = "b"

        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = NestedConfig()

        cfg = TestConfig()

        self.assertTrue(0 in cfg)
        self.assertTrue("ff" in cfg)
        self.assertTrue("a" in cfg)
        self.assertTrue("b" in cfg)

        self.assertFalse(99 in cfg)
        self.assertFalse("hh" in cfg)

        cfg.var3.var1 = 99

        self.assertTrue(0 in cfg)
        self.assertTrue("ff" in cfg)
        self.assertTrue(99 in cfg)
        self.assertTrue("b" in cfg)

    def test_object_to_list_1(self):
        """
        Tests that converting object instance to list yields expected list (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = 55.5

        cfg = TestConfig()
        self.assertEqual(['var1', 'var2', 'var3'], list(cfg))

    def test_object_to_list_2(self):
        """
        Tests that converting object instance to list yields expected list (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 2929
            var2 = (1,2,3)

        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = NestedConfig

        cfg = TestConfig()
        self.assertEqual(['var1', 'var2', 'var3.var1', 'var3.var2'], list(cfg))

    def test_object_to_tuple_1(self):
        """
        Tests that converting object instance to tuple yields expected tuple (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = 55.5

        cfg = TestConfig()
        self.assertEqual(('var1', 'var2', 'var3'), tuple(cfg))

    def test_object_to_tuple_2(self):
        """
        Tests that converting object instance to tuple yields expected tuple (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 2929
            var2 = (1,2,3)

        class TestConfig(VersionedObject):
            var1 = 0
            var2 = "ff"
            var3 = NestedConfig

        cfg = TestConfig()
        self.assertEqual(('var1', 'var2', 'var3.var1', 'var3.var2'), tuple(cfg))

    def test_object_len_1(self):
        """
        Tests that len() on an object instance returns the number of fields (no nested objects)
        """
        class TestConfig1(VersionedObject):
            val1 = 66
            val2 = 88
            srgg = 4456
            ftdj = 8888
            gg = 9

        class TestConfig2(VersionedObject):
            val1 = 66
            ftdj = 8888
            gg = 9

        cfg1 = TestConfig1()
        cfg2 = TestConfig2()
        self.assertEqual(5, len(cfg1))
        self.assertEqual(3, len(cfg2))

    def test_object_len_2(self):
        """
        Tests that len() on an object instance returns the number of fields (nested objects)
        """
        class NestedConfig(VersionedObject):
            ff = 99
            ll = 55
            gg = 77

        class TestConfig1(VersionedObject):
            val1 = 66
            val2 = 88
            srgg = 4456
            ftdj = 8888
            gg = NestedConfig()

        class TestConfig2(VersionedObject):
            val1 = 66
            ftdj = 8888
            gg = NestedConfig()

        cfg1 = TestConfig1()
        cfg2 = TestConfig2()
        self.assertEqual(7, len(cfg1))
        self.assertEqual(5, len(cfg2))
