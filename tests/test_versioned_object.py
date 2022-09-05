import os
from unittest import TestCase

from versionedobj import VersionedObject, LoadObjError, InvalidFilterError, CustomValue


class TestVersionedObject(TestCase):
    def test_basic_config_dict(self):
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        cfg = TestConfig()
        d = cfg.to_dict()

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        cfg.from_dict(d)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_dict_change(self):
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        cfg = TestConfig()
        d = cfg.to_dict()

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        d["val1"] = 12
        cfg.from_dict(d)

        self.assertEqual(12, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_json(self):
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        cfg = TestConfig()
        d = cfg.to_json()
        cfg.from_json(d)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

    def test_basic_config_file(self):
        class TestConfig(VersionedObject):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        cfg = TestConfig()
        filename = "__test_file.txt"
        cfg.to_file(filename)
        cfg.from_file(filename)

        self.assertEqual(1, cfg.val1)
        self.assertEqual(9.99, cfg.val2)
        self.assertEqual("howdy", cfg.val3)
        self.assertEqual([2, 3, 4], cfg.val4)
        self.assertEqual({"a": 5, "b": 55.5}, cfg.val5)

        os.remove(filename)

    def test_nested_config_dict(self):
        class NestedConfig(VersionedObject):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedObject):
            val1 = "a"
            val2 = NestedConfig()

        cfg = TestConfig()
        d = cfg.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        cfg.from_dict(d)

        self.assertEqual("a", cfg.val1)
        self.assertEqual(1, cfg.val2.val1)
        self.assertEqual(55.5, cfg.val2.val2)

    def test_nested_config_dict_change(self):
        class NestedConfig(VersionedObject):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedObject):
            val1 = "a"
            val2 = NestedConfig()

        cfg = TestConfig()
        d = cfg.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        d["val2"]["val2"] = "changed"
        cfg.from_dict(d)

        self.assertEqual("a", cfg.val1)
        self.assertEqual(1, cfg.val2.val1)
        self.assertEqual("changed", cfg.val2.val2)

    def test_load_dict_invalid_attr(self):
        class TestConfig(VersionedObject):
            val1 = 1

        cfg = TestConfig()
        self.assertRaises(LoadObjError, cfg.from_dict, {"val2": 55})

    def test_load_invalid_json(self):
        class TestConfig(VersionedObject):
            val1 = 1

        cfg = TestConfig()
        self.assertRaises(LoadObjError, cfg.from_json, "zsrg]s\er]gsegr")

    def test_load_dict_migration_failure_no_migrations(self):
        class TestConfig(VersionedObject):
            version = "1.0.0"
            value = 2727

        fake_config = {'version': '1.0.22', 'value': 2727}

        cfg = TestConfig()
        self.assertRaises(LoadObjError, cfg.from_dict, fake_config)

    def test_load_dict_migration_failure_bad_migration(self):
        class TestConfig(VersionedObject):
            version = "1.0.22"
            value = 2727

        fake_config = {'version': '1.0.0'}

        def bad_migration(attrs):
            return attrs

        TestConfig.add_migration('1.0.0', '1.0.21', bad_migration)

        cfg = TestConfig()
        self.assertRaises(LoadObjError, cfg.from_dict, fake_config)

    def test_load_dict_migration_success(self):
        class TestConfig(VersionedObject):
            version = '1.0.22'
            value1 = 2727
            value2 = 'hey'

        def migration(attrs):
            attrs['value2'] = 1234
            return attrs

        TestConfig.add_migration('1.0.0', '1.0.22', migration)

        fake_config = {'version': '1.0.0', 'value1': 8888}

        cfg = TestConfig()
        cfg.from_dict(fake_config)

        self.assertEqual(8888, cfg.value1)
        self.assertEqual(1234, cfg.value2)
        self.assertEqual('1.0.22', cfg.version)

    def test_load_dict_deeper_nesting(self):
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
        d = cfg.to_dict()

        self.assertEqual(3, d['val1'])
        self.assertEqual('gg', d['val2']['val1'])
        self.assertEqual(66.6, d['val2']['val2']['val1'])
        self.assertEqual(True, d['val2']['val2']['val2']['val1'])
        self.assertEqual(False, d['val2']['val2']['val2']['val2'])

        d['val2']['val1'] = "changed"
        cfg.from_dict(d)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('changed', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

    def test_load_json_deeper_nesting(self):
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
        d = cfg.to_json()
        cfg.from_json(d)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('gg', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

    def test_load_file_deeper_nesting(self):
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
        filename = "__test_cfg.txt"
        cfg.to_file(filename)
        cfg.from_file(filename)

        self.assertEqual(3, cfg.val1)
        self.assertEqual('gg', cfg.val2.val1)
        self.assertEqual(66.6, cfg.val2.val2.val1)
        self.assertEqual(True, cfg.val2.val2.val2.val1)
        self.assertEqual(False, cfg.val2.val2.val2.val2)

        os.remove(filename)

    def test_custom_value_to_dict_not_implemented(self):
        class TestCustomValue(CustomValue):
            def from_dict(self, data):
                pass

        class TestConfig(VersionedObject):
            val1 = TestCustomValue()

        cfg = TestConfig()
        self.assertRaises(NotImplementedError, cfg.to_dict)

    def test_custom_value_from_dict_not_implemented(self):
        class TestCustomValue(CustomValue):
            def to_dict(self):
                return {}

        class TestConfig(VersionedObject):
            val1 = TestCustomValue()

        cfg = TestConfig()
        d = cfg.to_dict()
        self.assertRaises(NotImplementedError, cfg.from_dict, d)

    def test_custom_value_success(self):
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

        cfg = TestConfig()

        d = cfg.to_dict()

        self.assertEqual(d['val2'], "1:2:3")

        # Change values in dict
        d['val2'] = "5:6:7"

        # Load values from dict
        cfg.from_dict(d)

        # Verify loaded values
        self.assertEqual(10, cfg.val1)
        self.assertEqual(5, cfg.val2.a)
        self.assertEqual(6, cfg.val2.b)
        self.assertEqual(7, cfg.val2.c)

    def test_to_dict_only_filter_1(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict(only=['var2'])
        self.assertEqual(1, len(d))
        self.assertEqual(2, d['var2'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_only_filter_2(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict(only=['var2', 'var3'])
        self.assertEqual(2, len(d))
        self.assertEqual(2, d['var2'])
        self.assertEqual(3, d['var3'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_only_filter_3(self):
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        cfg = TestConfig()

        d = cfg.to_dict(only=['var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual("abc", d['var3']['var1']['var1'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_to_dict_ignore_filter_1(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict(ignore=['var2'])
        self.assertEqual(2, len(d))
        self.assertEqual(1, d['var1'])
        self.assertEqual(3, d['var3'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_ignore_filter_2(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict(ignore=['var1', 'var2'])
        self.assertEqual(1, len(d))
        self.assertEqual(3, d['var3'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_to_dict_ignore_filter_3(self):
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        cfg = TestConfig()

        d = cfg.to_dict(ignore=['var1', 'var3.var1.var1'])
        self.assertEqual(1, len(d))
        self.assertEqual(2, d['var2'])

        cfg.from_dict(d)
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_to_dict_ignore_and_only_error(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        cfg = TestConfig()
        self.assertRaises(InvalidFilterError, cfg.to_dict, ['var1'], ['var1'])

    def test_from_dict_only_filter_1(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the values we're not loading
        d['var1'] = 99
        d['var2'] = 99

        cfg.from_dict(d, only=['var3'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_only_filter_2(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the value we're not loading
        d['var2'] = 99

        cfg.from_dict(d, only=['var1', 'var3'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_only_filter_3(self):
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        cfg = TestConfig()

        d = cfg.to_dict()

        # Change the value we're not loading
        d["var1"] = 99

        cfg.from_dict(d, only=['var2', 'var3.var1.var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_from_dict_ignore_filter_1(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the value we're ignoring
        d['var1'] = 99

        cfg.from_dict(d, ignore=['var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_ignore_filter_2(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the values we're ignoring
        d['var1'] = 99
        d['var2'] = 99

        cfg.from_dict(d, ignore=['var1', 'var2'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(3, cfg.var3)

    def test_from_dict_ignore_filter_3(self):
        class TestConfig2(VersionedObject):
            var1 = "abc"

        class TestConfig1(VersionedObject):
            var1 = TestConfig2()

        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = TestConfig1()

        cfg = TestConfig()

        d = cfg.to_dict()

        # Change the values we're ignoring
        d['var1'] = 99
        d['var3']['var1']['var1'] = "xxx"

        cfg.from_dict(d, ignore=['var1', 'var3.var1.var1'])
        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual("abc", cfg.var3.var1.var1)

    def test_from_dict_ignore_and_only_error(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        cfg = TestConfig()
        d = cfg.to_dict()
        self.assertRaises(InvalidFilterError, cfg.from_dict, d, ['var1'], ['var1'])

    def test_to_from_file_only_filter(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        filename = "__test_config.txt"
        cfg.to_file(filename)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        cfg.from_file(filename, only=['var1', 'var2'])

        self.assertEqual(1, cfg.var1)
        self.assertEqual(2, cfg.var2)
        self.assertEqual(99, cfg.var3)
        os.remove(filename)

    def test_to_from_file_ignore_filter(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2
            var3 = 3

        cfg = TestConfig()
        filename = "__test_config.txt"
        cfg.to_file(filename)

        # Change values in memory
        cfg.var1 = 99
        cfg.var2 = 99
        cfg.var3 = 99

        cfg.from_file(filename, ignore=['var2'])

        self.assertEqual(1, cfg.var1)
        self.assertEqual(99, cfg.var2)
        self.assertEqual(3, cfg.var3)
        os.remove(filename)

    def test_to_from_dict_two_instances_of_same_object(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

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

        d1 = cfg1.to_dict()
        d2 = cfg2.to_dict()

        d1['var1'] = 88
        d2['var1'] = 77

        cfg1.from_dict(d1)
        cfg2.from_dict(d2)

        self.assertEqual(88, cfg1.var1)
        self.assertEqual(99, cfg1.var2)
        self.assertEqual(77, cfg2.var1)
        self.assertEqual(100, cfg2.var2)

    def test_to_dict_only_subfields(self):
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig()
        d = cfg.to_dict(only=['var2'])

        self.assertEqual(1, len(d))
        self.assertEqual(2, len(d['var2']))
        self.assertEqual("hello", d['var2']['var1'])
        self.assertEqual(55.5, d['var2']['var2'])

    def test_to_dict_ignore_subfields(self):
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig()
        d = cfg.to_dict(ignore=['var2'])

        self.assertEqual(2, len(d))
        self.assertEqual(4, d['var1'])
        self.assertEqual(True, d['var3'])

    def test_from_dict_only_subfields(self):
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the values we're ignoring
        cfg.var1 = 99
        cfg.var3 = "sgghr"

        cfg.from_dict(d, only=['var2'])

        self.assertEqual(99, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual("sgghr", cfg.var3)

    def test_from_dict_ignore_subfields(self):
        class NestedConfig(VersionedObject):
            var1 = "hello"
            var2 = 55.5

        class TestConfig(VersionedObject):
            var1 = 4
            var2 = NestedConfig()
            var3 = True

        cfg = TestConfig()
        d = cfg.to_dict()

        # Change the fields we're ignoring
        d['var2']['var1'] = "xxx"
        d['var2']['var2'] = 99

        cfg.from_dict(d, ignore=['var2'])

        self.assertEqual(4, cfg.var1)
        self.assertEqual("hello", cfg.var2.var1)
        self.assertEqual(55.5, cfg.var2.var2)
        self.assertEqual(True, cfg.var3)

    def test_instantiation_with_initial_values(self):
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

    def test_add_migration_to_unversioned_obj(self):
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        def func(attrs):
            return attrs

        self.assertRaises(ValueError, TestConfig.add_migration, "a", "b", func)

    def test_migrate_unversioned_to_versioned(self):
        # New config, with version number added
        class TestConfig(VersionedObject):
            version = "1.0.0"
            var1 = 1
            var2 = 2
            var3 = 3

        # old config, different format, and without version number
        fake_config = {'var2': 12, 'var3': 13, 'var4': 14}

        # Add migration from unversioned to 1.0.0
        def migrate_none_to_100(attrs):
            del attrs['var4']
            attrs['var1'] = 11
            return attrs

        TestConfig.add_migration(None, "1.0.0", migrate_none_to_100)

        cfg = TestConfig()
        cfg.from_dict(fake_config)

        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)

        self.assertFalse(hasattr(cfg, 'var4'))

    def test_multiple_migrations(self):
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
        def migrate_none_to_100(attrs):
            attrs['var3'] = 13
            return attrs

        TestConfig.add_migration(None, "1.0.0", migrate_none_to_100)

        # Add migration from 1.0.0 to 1.0.1
        def migrate_100_to_101(attrs):
            attrs['var4'] = 14
            return attrs

        TestConfig.add_migration("1.0.0", "1.0.1", migrate_100_to_101)

        # Add migration from 1.0.1 to 1.0.2
        def migrate_101_to_102(attrs):
            attrs['var5'] = 15
            return attrs

        TestConfig.add_migration("1.0.1", "1.0.2", migrate_101_to_102)

        # Add migration from 1.0.2 to 1.0.3
        def migrate_102_to_103(attrs):
            attrs['var6'] = 16
            return attrs

        TestConfig.add_migration("1.0.2", "1.0.3", migrate_102_to_103)

        # Load oldest config from dict
        cfg = TestConfig()
        cfg.from_dict(fake_config)

        # Verify all migrations were performed
        self.assertEqual(11, cfg.var1)
        self.assertEqual(12, cfg.var2)
        self.assertEqual(13, cfg.var3)
        self.assertEqual(14, cfg.var4)
        self.assertEqual(15, cfg.var5)
        self.assertEqual(16, cfg.var6)
