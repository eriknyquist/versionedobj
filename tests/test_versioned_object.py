import os
from unittest import TestCase

from versionedobj import (VersionedObject, LoadObjectError, InvalidFilterError, Serializer,
    InputValidationError, InvalidVersionAttributeError, ObjectMigrationError, CustomValue, migration)


class TestVersionedObject(TestCase):
    def test_basic_config_dict(self):
        """
        Tests that a VersionedObject instance still contains the same values after
        being serialized to a dict and deserialized bback from the dict
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        s = Serializer()
        cfg = TestConfig()
        d = s.to_dict(cfg)

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        s.from_dict(cfg, d)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_dict_change(self):
        """
        Tests that we can change instance attributes on a VersionedObject instance,
        then serialize it to a dict, then deserialize it back from the dict, and see
        the same values that we changed on the instance attribute
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        s = Serializer()
        cfg = TestConfig()
        d = s.to_dict(cfg)

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        d["val1"] = 12
        s.from_dict(cfg, d)

        self.assertEqual(12, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_json(self):
        """
        Tests that a VersionedObject instance still contains the same values after
        being serialized to a JSON string and deserialized back from the JSON string
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        s = Serializer()
        cfg = TestConfig()
        d = s.to_json(cfg)
        s.from_json(cfg, d)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_file(self):
        """
        Tests that a VersionedObject instance still contains the same values after
        being serialized to a JSON file and deserialized back from the JSON file
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        s = Serializer()
        cfg = TestConfig()
        filename = "__test_file.txt"
        s.to_file(cfg, filename)
        s.from_file(cfg, filename)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

        os.remove(filename)

    def test_nested_config_dict(self):
        """
        Tests that a VersionedObject instance with nested VersionedObjbects still
        contains the same values after being serialized to a dict and deserialized
        back from the dict
        """
        class NestedConfig(VersionedObject):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedObject):
            val1 = "a"
            val2 = NestedConfig()

        s = Serializer()
        cfg = TestConfig()
        d = s.to_dict(cfg)

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        s.from_dict(cfg, d)

        self.assertEqual("a", cfg.val1)
        self.assertEqual(1, cfg.val2.val1)
        self.assertEqual(55.5, cfg.val2.val2)

    def test_nested_config_dict_change(self):
        """
        Tests that we can change instance attributes on a VersionedObject instance
        with nested VersionedObjects, then serialize it to a dict, then deserialize
        it back from the dict, and see the same values that we changed on the instance
        attribute.
        """
        class NestedConfig(VersionedObject):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedObject):
            val1 = "a"
            val2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        d["val2"]["val2"] = "changed"
        ser.from_dict(cfg, d)

        self.assertEqual("a", cfg.val1)
        self.assertEqual(1, cfg.val2.val1)
        self.assertEqual("changed", cfg.val2.val2)

    def test_load_dict_invalid_attr_1(self):
        """
        Tests that load_dict raises the expected exception when an unrecognized
        attribute name is seen in the dict (no nested objects)
        """
        class TestConfig(VersionedObject):
            val1 = 1

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InputValidationError, ser.from_dict, cfg, {"val2": 55})

    def test_load_dict_invalid_attr_2(self):
        """
        Tests that load_dict raises the expected exception when an unrecognized
        attribute name is seen in the dict (nested objects)
        """
        class NestedConfig(VersionedObject):
            val1 = "a"
            val2 = "bb"

        class TestConfig(VersionedObject):
            val1 = 1
            val2 = NestedConfig

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InputValidationError, ser.from_dict, cfg, {"val1": 1, "val2": {"val1": 1, "val2": 1, "val3": 1}})

    def test_load_dict_missing_attr_1(self):
        """
        Tests that load_dict raises the expected exception when an expected attribute
        name is missing from the dict (no nested objects)
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 2

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InputValidationError, ser.from_dict, cfg, {"val2": 55})

    def test_load_dict_missing_attr_2(self):
        """
        Tests that load_dict raises the expected exception when an expected attribute
        name is missing from the dict (nested objects)
        """
        class NestedConfig(VersionedObject):
            val1 = "g"
            val2 = True

        class TestConfig(VersionedObject):
            val1 = 1
            val2 = NestedConfig

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InputValidationError, ser.from_dict, cfg, {"val1": 99, "val2": {"val2": False}})

    def test_load_dict_missing_attr_no_validation_1(self):
        """
        Test that no exception is raised by load_dict, and that expected values are loaded,
        when an expected attribute name is missing from the dict but validate=False is set
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 2

        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, {"val2": 55}, validate=False)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(55, cfg.val2)

    def test_load_dict_missing_attr_no_validation_2(self):
        """
        Test that no exception is raised by load_dict, and that expected values are loaded,
        when an expected attribute name is missing from the dict but validate=False is set
        (nested objects)
        """
        class NestedConfig(VersionedObject):
            val1 = "g"
            val2 = True

        class TestConfig(VersionedObject):
            val1 = 1
            val2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, {"val1": 99, "val2": {"val2": 88}}, validate=False)

        self.assertEqual(99, cfg.val1)
        self.assertEqual("g", cfg.val2.val1)
        self.assertEqual(88, cfg.val2.val2)

    def test_from_json_invalid_json(self):
        """
        Tests that from_json raises expected exception when an invalid JSON string is provided
        """
        class TestConfig(VersionedObject):
            val1 = 1

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(LoadObjectError, ser.from_json, cfg, "zsrg]s\er]gsegr")

    def test_from_file_invalid_json(self):
        """
        Tests that from_file raises expected exception when a JSON file with invalid data is provided
        """
        class TestConfig(VersionedObject):
            val1 = 1

        filename = "__test_file.json"
        with open(filename, 'w') as fh:
            fh.write("zsrghjsgk[serk[hgkmjs[;g;w'rhg;'w")

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(LoadObjectError, ser.from_file, cfg, filename)

    def test_load_dict_migration_failure_no_migrations(self):
        """
        Tests that load_dict raises expected exception when migrations are required
        but no migrations have been added to the class
        """
        class TestConfig(VersionedObject):
            version = "1.0.0"
            value = 2727

        fake_config = {'version': '1.0.22', 'value': 2727}

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(ObjectMigrationError, ser.from_dict, cfg, fake_config)

    def test_load_dict_migration_failure_bad_migration_decorator(self):
        """
        Tests that load_dict raises expected exception when migrations exist
        but they do not migrate the object to the latest version (migration decorator)
        """
        class TestConfig(VersionedObject):
            version = "1.0.22"
            value = 2727

        fake_config = {'version': '1.0.0'}

        @migration(TestConfig, "1.0.0", "1.0.21")
        def bad_migration(attrs):
            return attrs

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(ObjectMigrationError, ser.from_dict, cfg, fake_config)

    def test_load_dict_migration_success_decorator_1(self):
        """
        Tests that we can successfully migrate an older object to a newer version
        which adds a new attribute (no nested objects) (migration decorator)
        """
        class TestConfig(VersionedObject):
            version = '1.0.22'
            value1 = 2727
            value2 = 'hey'

        @migration(TestConfig, "1.0.0", "1.0.22")
        def migration_func(attrs):
            attrs['value2'] = 1234
            return attrs

        fake_config = {'version': '1.0.0', 'value1': 8888}

        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, fake_config)

        self.assertEqual(8888, cfg.value1)
        self.assertEqual(1234, cfg.value2)
        self.assertEqual('1.0.22', cfg.version)

    def test_load_dict_migration_success_decorator_2(self):
        """
        Tests that we can successfully migrate an older object to a newer version
        which adds a new attribute (nested objects) (migration decorator)
        """
        class NestedConfig(VersionedObject):
            value1 = 88
            value2 = 99

        class TestConfig(VersionedObject):
            version = '1.0.22'
            value1 = 2727
            value2 = NestedConfig

        @migration(TestConfig, "1.0.0", "1.0.22")
        def migrate_100_to_1022(attrs):
            attrs['value2']['value2'] = 22
            return attrs

        fake_config = {'version': '1.0.0', 'value1': 8888, 'value2': {'value1': 11}}

        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, fake_config)

        self.assertEqual(8888, cfg.value1)
        self.assertEqual(11, cfg.value2.value1)
        self.assertEqual(22, cfg.value2.value2)
        self.assertEqual('1.0.22', cfg.version)

    def test_load_dict_deeper_nesting(self):
        """
        Tests serializing & deserializing a VersionedObject with 4 levels of nested
        obejcts with to_dict/from_dict
        """
        class Level4(VersionedObject):
            val1 = True
            val2 = False

        class Level3(VersionedObject):
            val1 = 66.6
            val2 = Level4()

        class Level2(VersionedObject):
            val1 = "gg"
            val2 = Level3()

        class Level1(VersionedObject):
            val1 = 3
            val2 = Level2()

        ser = Serializer()
        cfg = Level1()
        d = ser.to_dict(cfg)

        self.assertEqual(3, d['val1'])
        self.assertEqual('gg', d['val2']['val1'])
        self.assertEqual(66.6, d['val2']['val2']['val1'])
        self.assertEqual(True, d['val2']['val2']['val2']['val1'])
        self.assertEqual(False, d['val2']['val2']['val2']['val2'])

        d['val2']['val1'] = "changed"
        ser.from_dict(cfg, d)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('changed', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

    def test_load_json_deeper_nesting(self):
        """
        Tests serializing & deserializing a VersionedObject with 4 levels of nested
        obejcts with to_json/from_json
        """
        class Level4(VersionedObject):
            val1 = True
            val2 = False

        class Level3(VersionedObject):
            val1 = 66.6
            val2 = Level4()

        class Level2(VersionedObject):
            val1 = "gg"
            val2 = Level3()

        class Level1(VersionedObject):
            val1 = 3
            val2 = Level2()

        ser = Serializer()
        cfg = Level1()
        d = ser.to_json(cfg)
        ser.from_json(cfg, d)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('gg', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

    def test_load_file_deeper_nesting(self):
        """
        Tests serializing & deserializing a VersionedObject with 4 levels of nested
        obejcts with to_file/from_file
        """
        class Level4(VersionedObject):
            val1 = True
            val2 = False

        class Level3(VersionedObject):
            val1 = 66.6
            val2 = Level4()

        class Level2(VersionedObject):
            val1 = "gg"
            val2 = Level3()

        class Level1(VersionedObject):
            val1 = 3
            val2 = Level2()

        ser = Serializer()
        cfg = Level1()
        filename = "__test_cfg.txt"
        ser.to_file(cfg, filename)
        ser.from_file(cfg, filename)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('gg', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

        os.remove(filename)

    def test_custom_value_to_dict_not_implemented(self):
        """
        Tests that CustomValue instance raises expected exception when to_dict()
        is not implemented
        """
        class TestCustomValue(CustomValue):
            def from_dict(self, data):
                pass

        class TestConfig(VersionedObject):
            val1 = TestCustomValue()

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(NotImplementedError, ser.to_dict, cfg)

    def test_custom_value_from_dict_not_implemented(self):
        """
        Tests that CustomValue instance raises expected exception when from_dict()
        is not implemented
        """
        class TestCustomValue(CustomValue):
            def to_dict(self):
                return {}

        class TestConfig(VersionedObject):
            val1 = TestCustomValue()

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)
        self.assertRaises(NotImplementedError, ser.from_dict, cfg, d)

    def test_custom_value_success(self):
        """
        Tests that to_dict/from_dict correctly handles a CustomValue implementation
        with custom serialization format
        """
        class TestCustomValue(CustomValue):
            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

            def to_dict(self):
                return f"{self.a}:{self.b}:{self.c}"

            def from_dict(self, val):
                fields = val.split(':')
                self.a = int(fields[0])
                self.b = int(fields[1])
                self.c = int(fields[2])

        class TestConfig(VersionedObject):
            val1 = 10
            val2 = TestCustomValue(1, 2, 3)

        ser = Serializer()
        cfg = TestConfig()

        d = ser.to_dict(cfg)

        self.assertEqual(d['val2'], "1:2:3")

        # Change values in dict
        d['val2'] = "5:6:7"

        # Load values from dict
        ser.from_dict(cfg, d)

        # Verify loaded values
        self.assertEqual(10, cfg.val1)
        self.assertEqual(5, cfg.val2.a)
        self.assertEqual(6, cfg.val2.b)
        self.assertEqual(7, cfg.val2.c)

    def test_to_dict_only_filter_1(self):
        """
        Tests that to_dict produces a dict that only contains the attribute
        names in the 'only' filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, only=['var2'])
        self.assertEqual(1, len(d))
        self.assertEqual(2, d['var2'])

        ser.from_dict(cfg, d, validate=False)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_only_filter_2(self):
        """
        Tests that to_dict produces a dict that only contains the attribute
        names in the 'only' filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, only=['var2', 'var3'])
        self.assertEqual(2, len(d))
        self.assertEqual(2, d['var2'])
        self.assertEqual(3, d['var3'])

        ser.from_dict(cfg, d, validate=False)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_only_filter_3(self):
        """
        Tests that to_dict produces a dict that only contains the attribute
        names in the 'only' filter (nested objects)
        """
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        ser = Serializer()
        cfg = TestConfig()

        d = ser.to_dict(cfg, only=['var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual("abc", d['var3']['var1']['var1'])

        ser.from_dict(cfg, d, validate=False)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_to_dict_ignore_filter_1(self):
        """
        Tests that to_dict produces a dict that contains all attributes except those
        in the 'ignore' filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, ignore=['var2'])
        self.assertEqual(2, len(d))
        self.assertEqual(1, d['var1'])
        self.assertEqual(3, d['var3'])

        ser.from_dict(cfg, d, ignore=['var2'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_ignore_filter_2(self):
        """
        Tests that to_dict produces a dict that contains all attributes except those
        in the 'ignore' filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, ignore=['var1', 'var2'])
        self.assertEqual(1, len(d))
        self.assertEqual(3, d['var3'])

        ser.from_dict(cfg, d, validate=False)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_ignore_filter_3(self):
        """
        Tests that to_dict produces a dict that contains all attributes except those
        in the 'ignore' filter (nested objects)
        """
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        ser = Serializer()
        cfg = TestConfig()

        d = ser.to_dict(cfg, ignore=['var1', 'var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual(2, d['var2'])

        ser.from_dict(cfg, d, validate=False)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_to_dict_ignore_and_only_error(self):
        """
        Tests that to_dict raises expected exception when both non-empty 'ignore' and
        a non-empty 'only' lists are passed
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InvalidFilterError, ser.to_dict, cfg, ['var1'], ['var1'])

    def test_from_dict_only_filter_1(self):
        """
        Tests that from_dict only loads the attribute names in the 'only' filter
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the values we're not loading
        d['var1'] = 99
        d['var2'] = 99

        ser.from_dict(cfg, d, only=['var3'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_only_filter_2(self):
        """
        Tests that from_dict only loads the attribute names in the 'only' filter
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the value we're not loading
        d['var2'] = 99

        ser.from_dict(cfg, d, only=['var1', 'var3'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_only_filter_3(self):
        """
        Tests that from_dict only loads the attribute names in the 'only' filter
        (nested objects)
        """
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        ser = Serializer()
        cfg = TestConfig()

        d = ser.to_dict(cfg)

        # Change the value we're not loading
        d["var1"] = 99

        ser.from_dict(cfg, d, only=['var2', 'var3.var1.var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_from_dict_ignore_filter_1(self):
        """
        Tests that from_dict loads all attributes except those in the 'ignore'
        filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the value we're ignoring
        d['var1'] = 99

        ser.from_dict(cfg, d, ignore=['var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_ignore_filter_2(self):
        """
        Tests that from_dict loads all attributes except those in the 'ignore'
        filter (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the values we're ignoring
        d['var1'] = 99
        d['var2'] = 99

        ser.from_dict(cfg, d, ignore=['var1', 'var2'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_ignore_filter_3(self):
        """
        Tests that from_dict loads all attributes except those in the 'ignore'
        filter (nested objects)
        """
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        ser = Serializer()
        cfg = TestConfig()

        d = ser.to_dict(cfg)

        # Change the values we're ignoring
        d['var1'] = 99
        d['var3']['var1']['var1'] = "xxx"

        ser.from_dict(cfg, d, ignore=['var1', 'var3.var1.var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_from_dict_ignore_and_only_error(self):
        """
        Tests that from_dict raises expected exception when both non-empty 'ignore' and
        a non-empty 'only' lists are passed
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)
        self.assertRaises(InvalidFilterError, ser.from_dict, cfg, d, ignore=['var1'], only=['var1'])

    def test_to_from_file_only_filter(self):
        """
        Tests that to_file/from_file correctly handle the 'only' list
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        filename = "__test_config.txt"
        ser.to_file(cfg, filename)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        ser.from_file(cfg, filename, only=['var1', 'var2'])

        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(99, cfg.var3)
        os.remove(filename)

    def test_to_from_file_ignore_filter(self):
        """
        Tests that to_file/from_file correctly handle the 'ignore' list
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        ser = Serializer()
        cfg = TestConfig()
        filename = "__test_config.txt"
        ser.to_file(cfg, filename)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        ser.from_file(cfg, filename, ignore=['var2'])

        self.assertEqual(1, cfg.var1)
        self.assertEqual(99, cfg.var2)
        self.assertEqual(3, cfg.var3)
        os.remove(filename)

    def test_to_from_dict_two_instances_of_same_object(self):
        """
        Tests that we can create 2 instances of the same VersionedObject, and
        independently change their instance attributes, and independently serialize/deserialize them
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        ser = Serializer()
        cfg1 = TestConfig()
        cfg2 = TestConfig()

        cfg1.var1 = 99
        cfg1.var2 = 99
        cfg2.var1 = 100
        cfg2.var2 = 100

        self.assertEqual(99, cfg1.var1)
        self.assertEqual(99, cfg1.var2)
        self.assertEqual(100, cfg2.var1)
        self.assertEqual(100, cfg2.var2)

        d1 = ser.to_dict(cfg1)
        d2 = ser.to_dict(cfg2)

        d1['var1'] = 88
        d2['var1'] = 77

        ser.from_dict(cfg1, d1)
        ser.from_dict(cfg2, d2)

        self.assertEqual(88, cfg1.var1)
        self.assertEqual(99, cfg1.var2)
        self.assertEqual(77, cfg2.var1)
        self.assertEqual(100, cfg2.var2)

    def test_to_dict_only_subfields(self):
        """
        Tests that to_dict serializes the entire nested object, when the 'only'
        list contains the name of a nested VersionedObject
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, only=['var2'])

        self.assertEqual(1, len(d))
        self.assertEqual(2, len(d['var2']))
        self.assertEqual("hello", d['var2']['var1'])
        self.assertEqual(55.5, d['var2']['var2'])

    def test_to_dict_ignore_subfields(self):
        """
        Tests that to_dict excludes the entire nested object, when the 'ignore'
        list contains the name of a nested VersionedObject
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg, ignore=['var2'])

        self.assertEqual(2, len(d))
        self.assertEqual(4, d['var1'])
        self.assertEqual(True, d['var3'])

    def test_from_dict_only_subfields(self):
        """
        Tests that from_dict loads the entire nested object, when the 'only'
        list contains the name of a nested VersionedObject
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the values we're ignoring
        cfg.var1 = 99
        cfg.var3 = "sgghr"

        ser.from_dict(cfg, d, only=['var2'])

        self.assertEqual(99, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual("sgghr", cfg.var3)

    def test_from_dict_ignore_subfields(self):
        """
        Tests that from_dict excludes the entire nested object, when the 'ignore'
        list contains the name of a nested VersionedObject
        """
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        ser = Serializer()
        cfg = TestConfig()
        d = ser.to_dict(cfg)

        # Change the fields we're ignoring
        d['var2']['var1'] = "xxx"
        d['var2']['var2'] = 99

        ser.from_dict(cfg, d, ignore=['var2'])

        self.assertEqual(4, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

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

    def test_add_migration_to_unversioned_obj_decorator(self):
        """
        Tests that expected exception is raised when we attempt to add a migration
        to a VersionedObject without a 'version' attribute (migration decorator)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        raised = False
        try:
            @migration(TestConfig, "a", "b")
            def func(attrs):
                return attrs

        except ValueError:
            raised = True

        self.assertTrue(raised)

    def test_migrate_unversioned_to_versioned_decorator(self):
        """
        Tests that an unversioned object can be migrated to a versioned object
        (migration decorator)
        """
        # New config, with version number added
        class TestConfig(VersionedObject):
            version = "1.0.0"
            var1 = 1
            var2 = 2
            var3 = 3

        # old config, different format, and without version number
        fake_config = {'var2': 12, 'var3': 13, 'var4': 14}

        # Add migration from unversioned to 1.0.0
        @migration(TestConfig, None, "1.0.0")
        def migrate_none_to_100(attrs):
            del attrs['var4']
            attrs['var1'] = 11
            return attrs

        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, fake_config)

        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)

        self.assertFalse(hasattr(cfg, 'var4'))

    def test_multiple_migrations_decorator(self):
        """
        Tests that we can successfully migrate an obbject that is 4 versions old,
        to the latest version (migration decorator)
        """
        # Newest config, with version number added
        class TestConfig(VersionedObject):
            version = "1.0.3"
            var1 = 1
            var2 = 2
            var3 = 3
            var4 = 4
            var5 = 5
            var6 = 6

        # oldest config, different format, and without version number
        fake_config = {'var1': 11, 'var2': 12}

        # Add migration from unversioned to 1.0.0
        @migration(TestConfig, None, "1.0.0")
        def migrate_none_to_100(attrs):
            attrs['var3'] = 13
            return attrs

        # Add migration from 1.0.0 to 1.0.1
        @migration(TestConfig, "1.0.0", "1.0.1")
        def migrate_100_to_101(attrs):
            attrs['var4'] = 14
            return attrs

        # Add migration from 1.0.1 to 1.0.2
        @migration(TestConfig, "1.0.1", "1.0.2")
        def migrate_101_to_102(attrs):
            attrs['var5'] = 15
            return attrs

        # Add migration from 1.0.2 to 1.0.3
        @migration(TestConfig, "1.0.2", "1.0.3")
        def migrate_102_to_103(attrs):
            attrs['var6'] = 16
            return attrs

        # Load oldest config from dict
        ser = Serializer()
        cfg = TestConfig()
        ser.from_dict(cfg, fake_config)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)
        self.assertEqual(14, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)

    def test_validate_dict_missing_from_dict(self):
        """
        Tests that validate_dict raises expected exception when an expected
        attribute name is missing from the dict
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = 8.8

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        bad_config = {'var1': 1, 'var2': {'var1': "hey"}}

        self.assertRaises(InputValidationError, ser.validate_dict, cfg, bad_config)

    def test_validate_dict_invalid_dict_field_1(self):
        """
        Tests that validate_dict raises expected exception when an unexpected
        attribute name is present in the dict
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = 8.8

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        bad_config = {'var1': 1, 'var2': {'var1': "hey", 'var2': 8.8, 'bad': 5}}

        self.assertRaises(InputValidationError, ser.validate_dict, cfg, bad_config)

    def test_validate_dict_invalid_dict_field_2(self):
        """
        Tests that validate_dict raises expected exception when an unexpected
        attribute name is present in the dict
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = 8.8

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        bad_config = {'var1': 1, 'var2': {'var1': "hey", 'val2': 8.8}}

        self.assertRaises(InputValidationError, ser.validate_dict, cfg, bad_config)

    def test_validate_dict_invalid_filter(self):
        """
        Tests that validate_dict raises expected exception when both a non-empty 'only'
        list and a non-empty 'ignore' list are passed
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InvalidFilterError, ser.validate_dict, cfg, {}, only=['a'], ignore=['b'])

    def test_validate_dict_success(self):
        """
        Tests validate_dict in the happy path
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = 8.8

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        ser = Serializer()
        cfg = TestConfig()
        good_config = {'var1': 99, 'var2': {'var1': "heesgfsegy", 'var2': 10000}}
        ser.validate_dict(cfg, good_config)

        # Verify values from dict were not loaded
        self.assertEqual(1, cfg.var1)
        self.assertEqual("hey", cfg.var2.var1)
        self.assertEqual(8.8, cfg.var2.var2)

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

        for name, val in cfg:
            retrieved[name] = val

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

        for name, val in cfg:
            retrieved[name] = val

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

        for name, val in cfg:
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

        for name, val in cfg:
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

    def test_nested_version_exception_1(self):
        """
        Tests that expected exception is raised when a nested object has a 'version' attribute
        """
        class NestedConfig(VersionedObject):
            var1 = "hey"
            var2 = False
            version = "q"

        class TestConfig1(VersionedObject):
            var1 = 1
            var2 = NestedConfig()

        self.assertRaises(InvalidVersionAttributeError, TestConfig1)

    def test_nested_version_exception_2(self):
        """
        Tests that expected exception is raised when a nested object has a 'version' attribute
        """
        class NestedConfig1(VersionedObject):
            var1 = "hey"
            var2 = False
            version = 8

        class NestedConfig2(VersionedObject):
            var1 = "hey"
            var2 = NestedConfig1

        class TestConfig1(VersionedObject):
            var1 = 1
            var2 = NestedConfig2

        self.assertRaises(InvalidVersionAttributeError, TestConfig1)
