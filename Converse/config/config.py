# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import copy
from typing import Iterable, Tuple


class ConfigDictionary:
    """
    A simple wrapper around a dictionary type
    that supports two different ways to retrieve the value
    from the key for convenience & easier code search accessing the attribute.
    A. config.key
    B. config[key]

    Support most of the builtin functions of a dictionary, such as

    len(config)
    for x in config:
    print(config)
    x in config
    for k,v in config.items():

    should be supported
    """

    def __init__(self, dictionary: dict = None):
        if dictionary is None:
            dictionary = dict()
        self._keys = set(dictionary)
        for key, value in dictionary.items():
            self.__setattr__(key, value)

    def __repr__(self):
        d = self.__dict__.copy()
        del d["_keys"]  # remove keys attribute from printing
        return d.__repr__()

    def copy(self):
        """ Creates a deep copy of this instance """
        return copy.deepcopy(self)

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __contains__(self, item) -> bool:
        return item in self._keys

    def __iter__(self) -> Iterable[str]:
        return self._keys.__iter__()

    def items(self) -> Iterable[Tuple]:
        return ((key, self[key]) for key in self)

    def __len__(self) -> int:
        return len(self._keys)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for key, value in other.items():
            if key not in self._keys or value != self[key]:
                return False
        return True


class AllowedKeyConfigDictionary(ConfigDictionary):
    """
    A base class of a dictionary where its keys must be
    from a specified pool.
    """

    _AllowedKeys = {
        # a set of keys allowed
    }

    def __init__(self, dictionary: dict = None):
        super().__init__(dictionary)
        for key in self._keys:
            if key not in self._AllowedKeys:
                raise KeyError("Attribute %s not allowed" % key)


class FixedKeyConfigDictionary(ConfigDictionary):
    """
    A base class representing a dictionary
    where every key is fixed, i.e., either required or optional.
    During the initialization, it checks for every
    key in the input dictionary with required & optional keys.
    If the value of an optional key is None,
    it will be replaced by the default value in the optional attribute

    This class is to be used to validate a yaml configuration meets its expected format

    Every child class must specify its own set of required & optional
    attributes below

    Attributes:
        _REQUIRED_ATTRIBUTES: must be provided during initialization
            Each attribute's value will be checked to make sure
            the desired type is provided
        _OPTIONAL_ATTRIBUTES: may not be provided during initialization
            Each attribute's value will be type-cast to the provided
    """

    _REQUIRED_ATTRIBUTES = {
        # "key" : valueTYpe
        # to be specified by the child class
    }

    _OPTIONAL_ATTRIBUTES = {
        # "key" : defaultValue
        # to be specified by the child class
    }

    def __init__(self, dictionary: dict = None):
        if dictionary is None:
            dictionary = dict()
        super().__init__(dictionary)

        for key in self._keys:
            if (
                key not in self._REQUIRED_ATTRIBUTES
                and key not in self._OPTIONAL_ATTRIBUTES
            ):
                raise ValueError(
                    "Unrecognized attribute %s in %s" % (key, self.__class__.__name__)
                )

        for key, valueType in self._REQUIRED_ATTRIBUTES.items():
            if key not in dictionary:
                raise ValueError(
                    "Required attribute %s missing from %s"
                    % (key, self.__class__.__name__)
                )
            elif not isinstance(self[key], valueType) and self[key]:
                self.__setattr__(key, valueType(dictionary[key]))

        for key, defaultValue in self._OPTIONAL_ATTRIBUTES.items():
            if key not in dictionary or dictionary[key] is None:
                # if user did not provide this key,
                # or if user explicitly provided None,
                # we use the default value specified in the attribute
                self.__setattr__(key, defaultValue)
                self._keys.add(key)
            elif defaultValue is not None and not isinstance(
                self[key], type(defaultValue)
            ):
                # if not the type as expected, type cast
                self.__setattr__(key, type(defaultValue)(self[key]))


class ConfigDictionaryOfType(ConfigDictionary):
    """
    Every value of the dictionary must be of a specified object
    During the construction, will raise an exception if type is not matched
    or the value cannot be cast to the expected type

    To use this class, one must either
    1. inherit this class and specify _defaultType attribute, or
    2. use one of the static wrapper methods

    Attributes:
        defaultTYpe must be defined for all subclasses
    """

    _type = None

    def __init__(self, dictionary: dict = None):
        if dictionary is None:
            dictionary = dict()
        self._keys = set(dictionary)
        for key, value in dictionary.items():
            self.__setattr__(key, self._type(value))

    @classmethod
    def buildWith(cls, defaultType: type):
        """
        Wrapper to build and return the class itself with the default type provided
        """
        className = cls.__name__ + defaultType.__name__
        return type(className, (cls,), {"_type": defaultType})


class ConfigListOfType:
    """
    This class represents a list of the specified type
    It will validate the data upon initialization and
    try to cast to the desired type.
    If not possible, it will raise an implicit exception (during the casting)

    The class should behave just like a regular list

    Attribute:
        _type: desired type
    """

    _type = None

    def __init__(self, iterable: Iterable = None):
        self._values = []
        if iterable is None:
            iterable = []
        for value in iterable:
            self._values.append(self._type(value))

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, item):
        return self._values[item]

    def __iter__(self):
        return self._values.__iter__()

    def __repr__(self):
        return self._values.__repr__()

    def __eq__(self, other):
        return self._values == other

    @classmethod
    def buildWith(cls, defaultType: type):
        """
        Wrapper to build and return the class itself with the default type provided
        """
        className = cls.__name__ + defaultType.__name__
        return type(className, (cls,), {"_type": defaultType})


def DictionaryOfType(ofType: type) -> ConfigDictionaryOfType.__class__:
    """
    Wrapper function to create the desired typed dictionary more easily
    Warning: serialization/deserialization does not work
    """
    return ConfigDictionaryOfType.buildWith(ofType)


def ListOfType(ofType: type) -> ConfigListOfType.__class__:
    """
    Wrapper function to create the desired typed list more easily
    Warning: serialization/deserialization does not work
    """
    return ConfigListOfType.buildWith(ofType)


# some common classes
class ListOfStr(ConfigListOfType):
    _type = str


class DictionaryOfListOfStr(ConfigDictionaryOfType):
    _type = ListOfStr
