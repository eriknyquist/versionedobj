import os
from unittest import TestCase

from versionedconfig import VersionedConfig, LoadConfigError


class TestVersionedConfig(TestCase):
    def test_basic_config_dict(self):
        class TestConfig(VersionedConfig):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        d = TestConfig.to_dict()

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        TestConfig.from_dict(d)

        self.assertEqual(1, TestConfig.val1)
        self.assertEqual(9.99, TestConfig.val2)
        self.assertEqual("howdy", TestConfig.val3)
        self.assertEqual([2, 3, 4], TestConfig.val4)
        self.assertEqual({"a": 5, "b": 55.5}, TestConfig.val5)

    def test_basic_config_dict_change(self):
        class TestConfig(VersionedConfig):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        d = TestConfig.to_dict()

        self.assertEqual(1, d['val1'])
        self.assertEqual(9.99, d['val2'])
        self.assertEqual("howdy", d['val3'])
        self.assertEqual([2, 3, 4], d['val4'])
        self.assertEqual({"a": 5, "b": 55.5}, d['val5'])

        d["val1"] = 12
        TestConfig.from_dict(d)

        self.assertEqual(12, TestConfig.val1)
        self.assertEqual(9.99, TestConfig.val2)
        self.assertEqual("howdy", TestConfig.val3)
        self.assertEqual([2, 3, 4], TestConfig.val4)
        self.assertEqual({"a": 5, "b": 55.5}, TestConfig.val5)

    def test_basic_config_json(self):
        class TestConfig(VersionedConfig):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        d = TestConfig.to_json()
        TestConfig.from_json(d)

        self.assertEqual(1, TestConfig.val1)
        self.assertEqual(9.99, TestConfig.val2)
        self.assertEqual("howdy", TestConfig.val3)
        self.assertEqual([2, 3, 4], TestConfig.val4)
        self.assertEqual({"a": 5, "b": 55.5}, TestConfig.val5)

    def test_basic_config_file(self):
        class TestConfig(VersionedConfig):
            val1 = 1
            val2 = 9.99
            val3 = "howdy"
            val4 = [2,3,4]
            val5 = {"a": 5, "b": 55.5}

        filename = "__test_file.txt"
        TestConfig.to_file(filename)
        TestConfig.from_file(filename)

        self.assertEqual(1, TestConfig.val1)
        self.assertEqual(9.99, TestConfig.val2)
        self.assertEqual("howdy", TestConfig.val3)
        self.assertEqual([2, 3, 4], TestConfig.val4)
        self.assertEqual({"a": 5, "b": 55.5}, TestConfig.val5)

        os.remove(filename)

    def test_nested_config_dict(self):
        class NestedConfig(VersionedConfig):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedConfig):
            val1 = "a"
            val2 = NestedConfig

        d = TestConfig.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        TestConfig.from_dict(d)

        self.assertEqual("a", TestConfig.val1)
        self.assertEqual(1, TestConfig.val2.val1)
        self.assertEqual(55.5, TestConfig.val2.val2)

    def test_nested_config_dict_change(self):
        class NestedConfig(VersionedConfig):
            val1 = 1
            val2 = 55.5

        class TestConfig(VersionedConfig):
            val1 = "a"
            val2 = NestedConfig

        d = TestConfig.to_dict()

        self.assertEqual("a", d["val1"])
        self.assertEqual(1, d["val2"]["val1"])
        self.assertEqual(55.5, d["val2"]["val2"])

        d["val2"]["val2"] = "changed"
        TestConfig.from_dict(d)

        self.assertEqual("a", TestConfig.val1)
        self.assertEqual(1, TestConfig.val2.val1)
        self.assertEqual("changed", TestConfig.val2.val2)

    def test_load_dict_invalid_attr(self):
        class TestConfig(VersionedConfig):
            val1 = 1

        self.assertRaises(LoadConfigError, TestConfig.from_dict, {"val2": 55})

    def test_load_invalid_json(self):
        class TestConfig(VersionedConfig):
            val1 = 1

        self.assertRaises(LoadConfigError, TestConfig.from_json, "zsrg]s\er]gsegr")

    def test_load_dict_migration_failure_no_migrations(self):
        class TestConfig(VersionedConfig):
            version = "1.0.0"
            value = 2727

        fake_config = {'version': '1.0.22', 'value': 2727}

        self.assertRaises(LoadConfigError, TestConfig.from_dict, fake_config)

    def test_load_dict_migration_failure_bad_migration(self):
        class TestConfig(VersionedConfig):
            version = "1.0.22"
            value = 2727

        fake_config = {'version': '1.0.0'}

        def bad_migration(attrs):
            return attrs

        TestConfig.add_migration('1.0.0', '1.0.21', bad_migration)

        self.assertRaises(LoadConfigError, TestConfig.from_dict, fake_config)

    def test_load_dict_migration_success(self):
        class TestConfig(VersionedConfig):
            version = '1.0.22'
            value1 = 2727
            value2 = 'hey'

        def migration(attrs):
            attrs['value2'] = 1234
            return attrs

        TestConfig.add_migration('1.0.0', '1.0.22', migration)

        fake_config = {'version': '1.0.0', 'value1': 8888}

        TestConfig.from_dict(fake_config)

        self.assertEqual(8888, TestConfig.value1)
        self.assertEqual(1234, TestConfig.value2)
        self.assertEqual('1.0.22', TestConfig.version)
