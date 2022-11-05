import os
from unittest import TestCase

from versionedobj import (VersionedObject, Serializer, CustomValue, InputValidationError, LoadObjectError,
                          InvalidVersionAttributeError, InvalidFilterError)


class TestVersionedObjectExceptions(TestCase):
    def test_load_dict_invalid_attr_1(self):
        """
        Tests that load_dict raises the expected exception when an unrecognized
        attribute name is seen in the dict (no nested objects)
        """
        class TestConfig(VersionedObject):
            val1 = 1

        ser = Serializer()
        cfg = TestConfig()
        self.assertRaises(InputValidationError, ser.from_dict, {"val2": 55}, cfg)

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

        cfg = TestConfig()
        ser = Serializer(cfg)
        self.assertRaises(InputValidationError, ser.from_dict, {"val1": 1, "val2": {"val1": 1, "val2": 1, "val3": 1}})

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
        self.assertRaises(InputValidationError, ser.from_dict, {"val2": 55}, cfg)

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
        self.assertRaises(InputValidationError, ser.from_dict, {"val1": 99, "val2": {"val2": False}}, cfg)

    def test_from_json_invalid_json(self):
        """
        Tests that from_json raises expected exception when an invalid JSON string is provided
        """
        class TestConfig(VersionedObject):
            val1 = 1

        cfg = TestConfig()
        ser = Serializer(cfg)
        self.assertRaises(LoadObjectError, ser.from_json, "zsrg]s\er]gsegr")

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
        self.assertRaises(LoadObjectError, ser.from_file, filename, cfg)

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
        self.assertRaises(NotImplementedError, ser.from_dict, d, cfg)

    def test_to_dict_ignore_and_only_error(self):
        """
        Tests that to_dict raises expected exception when both non-empty 'ignore' and
        a non-empty 'only' lists are passed
        """
        class TestConfig(VersionedObject):
            var1 = 1
            var2 = 2

        cfg = TestConfig()
        ser = Serializer(cfg)
        self.assertRaises(InvalidFilterError, ser.to_dict, ignore=['var1'], only=['var1'])

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
        self.assertRaises(InvalidFilterError, ser.from_dict, d, cfg, ignore=['var1'], only=['var1'])

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

        self.assertRaises(InputValidationError, ser.validate_dict, bad_config, cfg)

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

        self.assertRaises(InputValidationError, ser.validate_dict, bad_config, cfg)

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

        self.assertRaises(InputValidationError, ser.validate_dict, bad_config, cfg)

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
        self.assertRaises(InvalidFilterError, ser.validate_dict, {}, cfg, only=['a'], ignore=['b'])

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
