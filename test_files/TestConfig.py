# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


import unittest

from Converse.config.config import (
    ConfigDictionary,
    ConfigDictionaryOfType,
    FixedKeyConfigDictionary,
    ListOfType,
    DictionaryOfType,
    AllowedKeyConfigDictionary,
)
from Converse.config.task_config import Task, TaskEntity
from Converse.utils.yaml_parser import load_tasks


class TestConfigObjects(unittest.TestCase):
    def setUp(self):
        self.dictionary = load_tasks("test_files/test_tasks.yaml")
        self.config = ConfigDictionary(self.dictionary)

    def test_config_retrieve(self):
        """
        Test whether we can retrieve the key in two ways
        1. by attribute, as in config.key
        2. by dictionary, as in config['key']
        """
        for key, value in self.dictionary.items():
            self.assertEqual(self.config[key], value)
            self.assertEqual(getattr(self.config, key), value)

    def test_config_len(self):
        self.assertEqual(len(self.dictionary), len(self.config))

    def test_config_iter(self):
        for key in self.config:
            self.assertIn(key, self.dictionary)

    def test_config_items(self):
        for key, value in self.config.items():
            self.assertEqual(self.dictionary[key], value)

    def test_config_contains(self):
        for key in self.dictionary:
            self.assertIn(key, self.config)


class TestFixedKeyConfigDictionary(unittest.TestCase):
    def setUp(self):
        self.dictionary = {
            "zero": 0,
            "zeroStr": "zero",
            "1": "one",
            "2": "",
            "None": None,
        }

    def test_config_correct_attributes(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                "zeroStr": str,
            }
            _OPTIONAL_ATTRIBUTES = {
                "1": "one",
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        expectedDictionary = {
            "zero": 0,  # required, as is
            "zeroStr": "zero",  # required, as is
            "1": "one",  # optional, as is
            "2": "",  # optional, as is
            "None": "StrVerOfNone",  # optional to default because user provided None
            "missingKey": 0,  # optional to default because not provided
        }
        config = SomeTestConfigClass(self.dictionary)
        for key, value in config.items():
            self.assertEqual(value, expectedDictionary[key])

    def test_config_missing_required_attribute(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                "zeroStr": str,
                "requiredKey": int,  # self.dictionary does not have this key
            }
            _OPTIONAL_ATTRIBUTES = {
                "1": "one",
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        with self.assertRaises(ValueError):
            SomeTestConfigClass(self.dictionary)

    def test_config_unexpected_attribute1(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                "zeroStr": str,
            }
            _OPTIONAL_ATTRIBUTES = {
                # '1': 'one', --> this is now an unexpected attribute
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        with self.assertRaises(ValueError):
            SomeTestConfigClass(self.dictionary)

    def test_config_unexpected_attribute2(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                # "zeroStr": str, --> this is now an unexpected attribute
            }
            _OPTIONAL_ATTRIBUTES = {
                "1": "one",
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        with self.assertRaises(ValueError):
            SomeTestConfigClass(self.dictionary)

    def test_config_required_type_mismatch(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                "zeroStr": int,  # type mismatch
            }
            _OPTIONAL_ATTRIBUTES = {
                "1": "one",
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        with self.assertRaises(ValueError):
            SomeTestConfigClass(self.dictionary)

    def test_config_optional_type_mismatch(self):
        class SomeTestConfigClass(FixedKeyConfigDictionary):
            _REQUIRED_ATTRIBUTES = {
                "zero": int,
                "zeroStr": str,
            }
            _OPTIONAL_ATTRIBUTES = {
                "1": 1,  # type mismatch
                "2": "two",
                "None": "StrVerOfNone",
                "missingKey": 0,
            }

        with self.assertRaises(ValueError):
            SomeTestConfigClass(self.dictionary)


class TestTypedDictionary1(unittest.TestCase):
    def setUp(self):
        self.dictionary = load_tasks("test_files/test_tasks.yaml")

    def test_with_correct_type(self):
        TaskConfigClass = ConfigDictionaryOfType.buildWith(Task)
        config = TaskConfigClass(self.dictionary)
        # successful initialization w/o exception means successful
        # but let us verify the keys just in case
        for key in self.dictionary:
            self.assertIn(key, config)

    def test_with_incorrect_type(self):
        TaskConfigClass = ConfigDictionaryOfType.buildWith(TaskEntity)
        with self.assertRaises(ValueError):
            TaskConfigClass(self.dictionary)


class TestTypedDictionary2(unittest.TestCase):
    def setUp(self):
        self.dictionary = {"a": "a", "one": 1}

    def test_with_acceptable_type(self):
        """
        int 1 can be cast into str "1"
        """
        expectedDictionary = {"a": "a", "one": "1"}
        config = DictionaryOfType(str)(self.dictionary)
        self.assertEqual(config, expectedDictionary)

    def test_with_wrong_type(self):
        with self.assertRaises(ValueError):
            DictionaryOfType(int)(self.dictionary)


class TestTypedList(unittest.TestCase):
    def setUp(self):
        self.list = [1, 2, 3, "one", "two", "three"]

    def test_with_acceptable_type(self):
        """
        1, 2, 3 can be cast into string "1", "2", "3"
        """
        expectedList = ["1", "2", "3", "one", "two", "three"]
        config = ListOfType(str)(self.list)
        self.assertEqual(config, expectedList)

    def test_with_wrong_type(self):
        with self.assertRaises(ValueError):
            ListOfType(int)(self.list)


class TestAllowedKeyConfigDictionary(unittest.TestCase):
    class TestDict(AllowedKeyConfigDictionary):
        _AllowedKeys = {
            "a",
            "b",
            "c",
        }

    def test_with_acceptable_keys(self):
        d = {
            "a": True,
            "b": "hi",
        }
        config = self.TestDict(d)
        self.assertEqual(config, d)

    def test_with_unknown_keys(self):
        d = {
            "a": True,
            "e": "not an allowed key and should throw an exception",
        }
        with self.assertRaises(KeyError):
            self.TestDict(d)
