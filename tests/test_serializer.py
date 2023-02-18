import os
from unittest import TestCase

from versionedobj import (VersionedObject, FileLoader, LoadObjectError, InvalidFilterError, Serializer, CustomValue, migration, List)


class TestVersionedObjectSerializer(TestCase):
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

        result = s.from_dict(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

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
        result = s.from_dict(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

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
        result = s.from_json(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        s = Serializer(cfg)
        filename = "__test_file.txt"
        s.to_file(filename)
        result = s.from_file(filename)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        s = Serializer(cfg)
        d = s.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        result = s.from_dict(d)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        d["val2"]["val2"] = "changed"
        result = ser.from_dict(d)
        self.assertIs(None, result) # verify no migrations peformewd

        self.assertEqual("a", cfg.val1)
        self.assertEqual(1, cfg.val2.val1)
        self.assertEqual("changed", cfg.val2.val2)

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
        result = ser.from_dict({"val2": 55}, cfg, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        result = ser.from_dict({"val1": 99, "val2": {"val2": 88}}, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd

        self.assertEqual(99, cfg.val1)
        self.assertEqual("g", cfg.val2.val1)
        self.assertEqual(88, cfg.val2.val2)

    def test_load_dict_migration_failure_no_migrations(self):
        """
        Tests that load_dict raises expected exception when migrations are required
        but no migrations have been added to the class
        """
        class TestConfig(VersionedObject):
            version = "1.0.22"
            value = 2727

        fake_config = {'version': '1.0.0', 'value': 2727}

        ser = Serializer()
        cfg = TestConfig()
        result = ser.from_dict(fake_config, cfg)

        self.assertEqual(False, result.success)
        self.assertEqual("1.0.0", result.old_version)
        self.assertEqual("1.0.22", result.target_version)
        self.assertEqual("1.0.0", result.version_reached)

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        result = ser.from_dict(fake_config)
        self.assertEqual(False, result.success)
        self.assertEqual("1.0.0", result.old_version)
        self.assertEqual("1.0.22", result.target_version)
        self.assertEqual("1.0.21", result.version_reached)

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        ser.from_dict(fake_config)

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        ser.from_dict(fake_config)

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
        result = ser.from_dict(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = Level1()
        ser = Serializer(cfg)
        d = ser.to_json(cfg)
        result = ser.from_json(d)
        self.assertIs(None, result) # verify no migrations peformewd

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
        ser.to_file(filename, cfg)
        result = ser.from_file(filename, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

        self.assertEqual(3, cfg.val1)
        self.assertEqual('gg', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

        os.remove(filename)

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
        result = ser.from_dict(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

        # Verify loaded values
        self.assertEqual(10, cfg.val1)
        self.assertEqual(5, cfg.val2.a)
        self.assertEqual(6, cfg.val2.b)
        self.assertEqual(7, cfg.val2.c)

    def test_custom_value_success_hotplug(self):
        """
        Tests that to_dict/from_dict correctly handles a CustomValue implementation
        with custom serialization format, when the CustomValue attribute is only set
        on the instance after class creation
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
            val2 = None

        ser = Serializer()
        cfg = TestConfig()
        cfg.val2 = TestCustomValue(1, 2, 3)

        d = ser.to_dict(cfg)

        self.assertEqual(d['val2'], "1:2:3")

        # Change values in dict
        d['val2'] = "5:6:7"

        # Load values from dict
        result = ser.from_dict(d, cfg)
        self.assertIs(None, result) # verify no migrations peformewd

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

        result = ser.from_dict(d, cfg, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict(only=['var2', 'var3'])
        self.assertEqual(2, len(d))
        self.assertEqual(2, d['var2'])
        self.assertEqual(3, d['var3'])

        result = ser.from_dict(d, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)

        d = ser.to_dict(only=['var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual("abc", d['var3']['var1']['var1'])

        result = ser.from_dict(d, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict(ignore=['var2'])
        self.assertEqual(2, len(d))
        self.assertEqual(1, d['var1'])
        self.assertEqual(3, d['var3'])

        result = ser.from_dict(d, ignore=['var2'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict(ignore=['var1', 'var2'])
        self.assertEqual(1, len(d))
        self.assertEqual(3, d['var3'])

        result = ser.from_dict(d, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)

        d = ser.to_dict(ignore=['var1', 'var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual(2, d['var2'])

        result = ser.from_dict(d, validate=False)
        self.assertIs(None, result) # verify no migrations peformewd
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_from_dict_only_filter_1(self):
        """
        Tests that from_dict only loads the attribute names in the 'only' filter
        (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the values we're not loading
        d['var1'] = 99
        d['var2'] = 99

        result = ser.from_dict(d, only=['var3'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the value we're not loading
        d['var2'] = 99

        result = ser.from_dict(d, only=['var1', 'var3'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)

        d = ser.to_dict()

        # Change the value we're not loading
        d["var1"] = 99

        result = ser.from_dict(d, only=['var2', 'var3.var1.var1'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the value we're ignoring
        d['var1'] = 99

        result = ser.from_dict(d, ignore=['var1'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the values we're ignoring
        d['var1'] = 99
        d['var2'] = 99

        result = ser.from_dict(d, ignore=['var1', 'var2'])
        self.assertIs(None, result) # verify no migrations peformewd
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

        cfg = TestConfig()
        ser = Serializer(cfg)

        d = ser.to_dict()

        # Change the values we're ignoring
        d['var1'] = 99
        d['var3']['var1']['var1'] = "xxx"

        result = ser.from_dict(d, ignore=['var1', 'var3.var1.var1'])
        self.assertIs(None, result) # verify no migrations peformewd
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

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
        ser.to_file(filename, cfg)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        result = ser.from_file(filename, cfg, only=['var1', 'var2'])
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        filename = "__test_config.txt"
        ser.to_file(filename)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        result = ser.from_file(filename, ignore=['var2'])
        self.assertIs(None, result) # verify no migrations peformewd

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

        result = ser.from_dict(d1, cfg1)
        self.assertIs(None, result) # verify no migrations peformewd
        result = ser.from_dict(d2, cfg2)
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict(only=['var2'])

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict(ignore=['var2'])

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the values we're ignoring
        cfg.var1 = 99
        cfg.var3 = "sgghr"

        result = ser.from_dict(d, only=['var2'])
        self.assertIs(None, result) # verify no migrations peformewd

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        d = ser.to_dict()

        # Change the fields we're ignoring
        d['var2']['var1'] = "xxx"
        d['var2']['var2'] = 99

        result = ser.from_dict(d, ignore=['var2'])
        self.assertIs(None, result) # verify no migrations peformewd

        self.assertEqual(4, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        ser.from_dict(fake_config)

        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)

        self.assertFalse(hasattr(cfg, 'var4'))

    def test_multiple_migration_path_failed_1(self):
        """
        Tests that the migration path fails as expected, when an object is 4 versions old
        but only 3 migrations are available
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

        # Load oldest config from dict
        cfg = TestConfig()
        ser = Serializer(cfg)
        result = ser.from_dict(fake_config)

        self.assertEqual(False, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.2", result.version_reached)

    def test_multiple_migration_path_failed_2(self):
        """
        Tests that the migration path fails as expected, when an object is 4 versions old
        but only 2 migrations are available
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

        # Load oldest config from dict
        cfg = TestConfig()
        ser = Serializer(cfg)
        result = ser.from_dict(fake_config)

        self.assertEqual(False, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.1", result.version_reached)

    def test_multiple_migration_path_failed_3(self):
        """
        Tests that the migration path fails as expected, when an object is 4 versions old
        but only 1 migrations is available
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

        # Load oldest config from dict
        ser = Serializer()
        cfg = TestConfig()
        result = ser.from_dict(fake_config, cfg)

        self.assertEqual(False, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.0", result.version_reached)

    def test_dict_multiple_migrations_1(self):
        """
        Tests that from_dict can successfully migrate an object that is 4 versions old,
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
        result = ser.from_dict(fake_config, cfg)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)
        self.assertEqual(14, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)

        self.assertEqual(True, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.3", result.version_reached)

    def test_dict_multiple_migrations_2(self):
        """
        Tests that from_dict can successfully migrate an object that is 3 versions old,
        when there are 4 versions total, to the latest version (migration decorator)
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
        fake_config = {'version': '1.0.1', 'var1': 11, 'var2': 12, 'var3': 113, 'var4': 114}

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
        result = ser.from_dict(fake_config, cfg)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(113, cfg.var3)
        self.assertEqual(114, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)

        self.assertEqual(True, result.success)
        self.assertEqual("1.0.1", result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.3", result.version_reached)

    def test_json_multiple_migrations(self):
        """
        Tests that from_json can successfully migrate an object that is 4 versions old,
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
        fake_config = '{"var1": 11, "var2": 12}'

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
        result = ser.from_json(fake_config, cfg)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)
        self.assertEqual(14, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)

        self.assertEqual(True, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.3", result.version_reached)

    def test_file_multiple_migrations(self):
        """
        Tests that from_file can successfully migrate an object that is 4 versions old,
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
        filename = "__test_file.txt"
        with open(filename, "w") as fh:
            fh.write('{"var1": 11, "var2": 12}')

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
        cfg = TestConfig()
        ser = Serializer(cfg)
        result = ser.from_file(filename)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)
        self.assertEqual(14, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)

        self.assertEqual(True, result.success)
        self.assertEqual(None, result.old_version)
        self.assertEqual("1.0.3", result.target_version)
        self.assertEqual("1.0.3", result.version_reached)

        os.remove(filename)

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
        ser.validate_dict(good_config, cfg)

        # Verify values from dict were not loaded
        self.assertEqual(1, cfg.var1)
        self.assertEqual("hey", cfg.var2.var1)
        self.assertEqual(8.8, cfg.var2.var2)

    def test_reset_to_defaults_1(self):
        """
        Tests that reset_to_defaults correctly resets all object attributes
        back to default class attribute values (no nested objects)
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "abc"
            var3 = 4.4

        cfg = TestConfig()
        ser = Serializer(cfg)

        self.assertEqual(1, cfg.var1)
        self.assertEqual("abc", cfg.var2)
        self.assertEqual(4.4, cfg.var3)

        # Change instance attribute values
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99
        self.assertEqual(99, cfg.var1)
        self.assertEqual(99, cfg.var2)
        self.assertEqual(99, cfg.var3)

        # Reset instance attribute values back to defaults and verify
        ser.reset_to_defaults(cfg)

        self.assertEqual(1, cfg.var1)
        self.assertEqual("abc", cfg.var2)
        self.assertEqual(4.4, cfg.var3)

    def test_reset_to_defaults_2(self):
        """
        Tests that reset_to_defaults correctly resets all object attributes
        back to default class attribute values (nested objects)
        """
        class NestedConfig(VersionedObject):
            var1 = 88
            var2 = "hey"
            var3 = 5.5

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = "abc"
            var3 = NestedConfig

        ser = Serializer()
        cfg = TestConfig()

        self.assertEqual(1, cfg.var1)
        self.assertEqual("abc", cfg.var2)
        self.assertEqual(88, cfg.var3.var1)
        self.assertEqual("hey", cfg.var3.var2)
        self.assertEqual(5.5, cfg.var3.var3)

        # Change instance attribute values
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3.var1 = 99
        cfg.var3.var2 = 99
        cfg.var3.var3 = 99
        self.assertEqual(99, cfg.var1)
        self.assertEqual(99, cfg.var2)
        self.assertEqual(99, cfg.var3.var1)
        self.assertEqual(99, cfg.var3.var2)
        self.assertEqual(99, cfg.var3.var3)

        # Reset instance attribute values back to defaults and verify
        ser.reset_to_defaults(cfg)

        self.assertEqual(1, cfg.var1)
        self.assertEqual("abc", cfg.var2)
        self.assertEqual(88, cfg.var3.var1)
        self.assertEqual("hey", cfg.var3.var2)
        self.assertEqual(5.5, cfg.var3.var3)

    def test_file_loader_success_1(self):
        """
        Tests that file loader serializes and deserializes object data from file
        as expected, when the file already exists
        """
        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = 33

        cfg = TestConfig()
        ser = Serializer(cfg)
        cfg.var1 = 44
        cfg.var2 = 55
        cfg.var3 = 66

        filename = "__test_config.txt"
        ser.to_file(filename)

        with FileLoader(TestConfig, filename) as obj:
            self.assertEqual(44, obj.var1)
            self.assertEqual(55, obj.var2)
            self.assertEqual(66, obj.var3)
            obj.var1 = 77
            obj.var2 = 88
            obj.var3 = 99

        ser.from_file(filename)
        self.assertEqual(77, cfg.var1)
        self.assertEqual(88, cfg.var2)
        self.assertEqual(99, cfg.var3)

        os.remove(filename)

    def test_file_loader_success_2(self):
        """
        Tests that file loader serializes and deserializes object data from file
        as expected, when the file does not already exist
        """
        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = 33

        ser = Serializer()
        cfg = TestConfig()
        cfg.var1 = 44
        cfg.var2 = 55
        cfg.var3 = 66

        filename = "__test_config.txt"
        with FileLoader(TestConfig, filename) as obj:
            self.assertEqual(11, obj.var1)
            self.assertEqual(22, obj.var2)
            self.assertEqual(33, obj.var3)

            obj.var1 = 77
            obj.var2 = 88
            obj.var3 = 99

        ser.from_file(filename, cfg)
        self.assertEqual(77, cfg.var1)
        self.assertEqual(88, cfg.var2)
        self.assertEqual(99, cfg.var3)

        os.remove(filename)

    def test_file_loader_invalid_objtype(self):
        """
        Tests that file loader raises expected exception when invalid object type
        is passed
        """
        filename = "__test_config.txt"
        self.assertRaises(ValueError, FileLoader, 4, filename)
        self.assertRaises(ValueError, FileLoader, 4.5, filename)
        self.assertRaises(ValueError, FileLoader, True, filename)
        self.assertRaises(ValueError, FileLoader, [12], filename)
        self.assertRaises(ValueError, FileLoader, {12:2}, filename)

    def test_to_from_dict_type_list_1(self):
        """
        Tests that a VersionedObject containing a types.List object is serialized to,
        and deserialized from a dict as expected
        """
        class TestVal1(VersionedObject):
            var1 = 55
            var2 = 66

        class TestVal2(VersionedObject):
            var1 = 33
            var2 = 44
            var3 = TestVal1()

        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = List([TestVal2(), TestVal2()])

        ser = Serializer()
        cfg = TestConfig()

        expected_dict = {
            'var1': 11,
            'var2': 22,
            'var3': [
                {'var1': 33, 'var2': 44, 'var3': {'var1': 55, 'var2': 66}},
                {'var1': 33, 'var2': 44, 'var3': {'var1': 55, 'var2': 66}},
            ],
        }

        cfg2 = TestConfig()
        actual_dict = ser.to_dict(cfg)
        self.assertEqual(actual_dict, expected_dict)

        ser.from_dict(actual_dict, cfg2)

        self.assertEqual(cfg2.var1, cfg.var1)
        self.assertEqual(cfg2.var2, cfg.var2)
        self.assertEqual(cfg2.var3[0].var1, cfg.var3[0].var1)
        self.assertEqual(cfg2.var3[0].var2, cfg.var3[0].var2)
        self.assertEqual(cfg2.var3[1].var1, cfg.var3[1].var1)
        self.assertEqual(cfg2.var3[1].var2, cfg.var3[1].var2)

    def test_to_from_dict_type_list_2(self):
        """
        Tests that a VersionedObject containing a types.List object is serialized to,
        and deserialized from a dict as expected
        """
        class TestVal1(VersionedObject):
            var1 = 55
            var2 = 66

        class TestVal2(VersionedObject):
            var1 = 33
            var2 = 44
            var3 = TestVal1()

        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = List(TestVal2)

        ser = Serializer()
        cfg = TestConfig()

        cfg.var3.append(TestVal2())
        cfg.var3.append(TestVal2())
        cfg.var3[0].var1 = 1
        cfg.var3[0].var2 = 2
        cfg.var3[0].var3.var1 = 3
        cfg.var3[0].var3.var2 = 4
        cfg.var3[1].var1 = 5
        cfg.var3[1].var2 = 6
        cfg.var3[1].var3.var1 = 7
        cfg.var3[1].var3.var2 = 8

        expected_dict = {
            'var1': 11,
            'var2': 22,
            'var3': [
                {'var1': 1, 'var2': 2, 'var3': {'var1': 3, 'var2': 4}},
                {'var1': 5, 'var2': 6, 'var3': {'var1': 7, 'var2': 8}},
            ],
        }

        cfg2 = TestConfig()
        actual_dict = ser.to_dict(cfg)
        self.assertEqual(actual_dict, expected_dict)

        ser.from_dict(actual_dict, cfg2)

        self.assertEqual(cfg2.var1, cfg.var1)
        self.assertEqual(cfg2.var2, cfg.var2)
        self.assertEqual(cfg2.var3[0].var1, cfg.var3[0].var1)
        self.assertEqual(cfg2.var3[0].var2, cfg.var3[0].var2)
        self.assertEqual(cfg2.var3[1].var1, cfg.var3[1].var1)
        self.assertEqual(cfg2.var3[1].var2, cfg.var3[1].var2)

    def test_to_from_json_type_list_1(self):
        """
        Tests that a VersionedObject containing a types.List object is serialized to,
        and deserialized from a JSON string as expected
        """
        class TestVal1(VersionedObject):
            var1 = 55
            var2 = 66

        class TestVal2(VersionedObject):
            var1 = 33
            var2 = 44
            var3 = TestVal1()

        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = List([TestVal2(), TestVal2()])

        ser = Serializer()
        cfg = TestConfig()

        expected_json = ('{"var1": 11, "var2": 22, "var3": [{"var1": 33, "var2":'
                         ' 44, "var3": {"var1": 55, "var2": 66}}, {"var1": 33, '
                         '"var2": 44, "var3": {"var1": 55, "var2": 66}}]}')

        cfg2 = TestConfig()
        actual_json = ser.to_json(cfg)
        self.assertEqual(actual_json, expected_json)

        ser.from_json(actual_json, cfg2)

        self.assertEqual(cfg2.var1, cfg.var1)
        self.assertEqual(cfg2.var2, cfg.var2)
        self.assertEqual(cfg2.var3[0].var1, cfg.var3[0].var1)
        self.assertEqual(cfg2.var3[0].var2, cfg.var3[0].var2)
        self.assertEqual(cfg2.var3[1].var1, cfg.var3[1].var1)
        self.assertEqual(cfg2.var3[1].var2, cfg.var3[1].var2)

    def test_to_from_json_type_list_2(self):
        """
        Tests that a VersionedObject containing a types.List object is serialized to,
        and deserialized from a JSON string as expected
        """
        class TestVal1(VersionedObject):
            var1 = 55
            var2 = 66

        class TestVal2(VersionedObject):
            var1 = 33
            var2 = 44
            var3 = TestVal1()

        class TestConfig(VersionedObject):
            var1 = 11
            var2 = 22
            var3 = List(TestVal2)

        ser = Serializer()
        cfg = TestConfig()

        cfg.var3.append(TestVal2())
        cfg.var3.append(TestVal2())
        cfg.var3[0].var1 = 1
        cfg.var3[0].var2 = 2
        cfg.var3[0].var3.var1 = 3
        cfg.var3[0].var3.var2 = 4
        cfg.var3[1].var1 = 5
        cfg.var3[1].var2 = 6
        cfg.var3[1].var3.var1 = 7
        cfg.var3[1].var3.var2 = 8

        expected_json = ('{"var1": 11, "var2": 22, "var3": [{"var1": 1, "var2": '
                         '2, "var3": {"var1": 3, "var2": 4}}, {"var1": 5, "var2": '
                         '6, "var3": {"var1": 7, "var2": 8}}]}')

        cfg2 = TestConfig()
        actual_json = ser.to_json(cfg)
        self.assertEqual(actual_json, expected_json)

        ser.from_json(actual_json, cfg2)

        self.assertEqual(cfg2.var1, cfg.var1)
        self.assertEqual(cfg2.var2, cfg.var2)
        self.assertEqual(cfg2.var3[0].var1, cfg.var3[0].var1)
        self.assertEqual(cfg2.var3[0].var2, cfg.var3[0].var2)
        self.assertEqual(cfg2.var3[1].var1, cfg.var3[1].var1)
        self.assertEqual(cfg2.var3[1].var2, cfg.var3[1].var2)
