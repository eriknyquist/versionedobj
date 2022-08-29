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

    def test_load_dict_invalid_attr(self):
        class TestConfig(VersionedConfig):
            val1 = 1

        self.assertRaises(LoadConfigError, TestConfig.from_dict, {"val2": 55})

    def test_load_invalid_json(self):
        class TestConfig(VersionedConfig):
            val1 = 1

        self.assertRaises(LoadConfigError, TestConfig.from_json, "zsrg]s\er]gsegr")
