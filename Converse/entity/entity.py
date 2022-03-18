# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from datetime import date, time
from enum import Enum
import sys
import re
from typing import Any, List, Tuple, Iterable

from thefuzz import process, fuzz
from Converse.nlu.ner_converse.client import NER
from num2words import num2words


class ExtractionMethod(Enum):
    NER = 1
    SPELLING = 2
    FUZZY_LOGIC = 3
    REGEX = 4
    USER_UTTERANCE = 5


class Entity(object):
    """
    Represent a single entity extracted from various methods
    Every entity type must subclass this object and implement some required
    methods, as well as value_types below

    Attributes:
        value_types (class): type(s) of the value it holds (string, int, double,
            custom object, etc)
            NOTE: value_types must be hashable!! (such as int, double, string)
            If a custom object is to be used, make it a hashable object
    """

    value_types = None

    def __init__(
        self,
        score: float,
        method: ExtractionMethod,
        user_utt_value,
        normalized_value=None,
        label: str = "",
        span: dict = None,
    ):
        """
        score: likely score (higher the more likely)
        method: extraction method
        user_utt_value: entity value extracted from the user utterance. Must be of type
            value_types or normalized_value must be of type value_types.
        normalized_value: normalized version of user_utt_value. Currently, this
            field is used for storing Duckling outputs. Must be of type value_types or
             user_utt_value must be of type value_types. (defaults to None)
        label: label from NER model, such EMAIL, PERSON, DATE, etc; not set
            for other methods
        span: A dictionary that represents that start and end index of the entity in
            the user utterance. It contains the keys "start" that maps to the starting
            index and "end" that maps to the ending index. If "start" is not in the
            dictionary, then the start index is 0. This method converts this dictionary
            into a tuple where the first element is the start index and the second
            element is the end index. We use a tuple to represent the span because
            we want the entity object to be hashable and dictionary objects are not
            hashable because they are mutable and tuples are hashable.

        Attributes:
            value (value_types): entity value representation; again, this object
                must be hashable
        """
        assert isinstance(user_utt_value, self.value_types) or isinstance(
            normalized_value, self.value_types
        )
        self.score: float = score
        self.method = method
        self.user_utt_value = user_utt_value
        self.normalized_value = normalized_value
        self.ner_label = label
        if span:
            start = 0
            if "start" in span:
                start = span["start"]
            span = (start, span["end"])
        self.span = span
        self.turn: int = None  # turn from which the entity was retrieved

    @property
    def value(self):
        """Returns the value of the entity. If normalized_value is set, this property
        returns normalized_value. Otherwise, it returns user_utt_value.
        """
        return self.normalized_value or self.user_utt_value

    def display_value(self) -> str:
        """Returns the human readable format of the value."""
        return str(self.value)

    @classmethod
    def from_ner_model(cls, ner_model_output: dict):
        """
        Construct an entity from the given NER candidate of the model output

        This is a required method that needs to be implemented for each type of
        entity. NamedEntityExtractor.extract will call this method
        """
        raise NotImplementedError

    @classmethod
    def from_spelling(cls, utterance: str):
        """
        Construct an entity from the cleaned-up utterance string

        This is a required method that needs to be implemented for each type of
        entity. SpellingEntityExtractor.extract will call this method
        """
        raise NotImplementedError

    def __repr__(self):
        """
        String representation of this entity
        """
        d = self.__dict__.copy()
        d["name"] = self.__class__.__name__
        return d.__repr__()

    def __eq__(self, other) -> bool:
        """
        If the types are exactly the same and if all the attributes are
        equal-valued, two entities are said to be equal
        """
        return type(self) == type(other) and self.__key() == other.__key()

    def __hash__(self):
        """
        Hash is simply from the tuple of the key attributes
        """
        return hash(self.__key())

    def __key(self) -> Tuple:
        """
        A tuple of all attributes
        """
        # self.__dict__ preserves the order for python >= 3.6
        assert sys.version_info >= (
            3,
            6,
        ), "Python version >= 3.6 is required for this to work properly"
        return tuple(self.__dict__.values())

    @classmethod
    def unique(cls, entities: Iterable["Entity"]) -> List["Entity"]:
        """
        Given a list of entities, return unique entities by its values.
        If there are multiple entities of the same value or the same user utterance
        value in the user utterance, single out the one with the highest score.
        """
        entities_filtered_by_value = cls.unique_by_value(entities)
        return cls.unique_by_user_utt_value(entities_filtered_by_value)

    @classmethod
    def unique_by_value(cls, entities: Iterable["Entity"]) -> List["Entity"]:
        """
        Given a list of entities, return unique entities by its values.
        If there are multiple entities of the same value, single out the one with the
        highest score.
        """
        entity_dict = dict()
        for entity in entities:
            value, score = entity.value, entity.score
            if value not in entity_dict or entity_dict[value].score < score:
                entity_dict[value] = entity
        return list(entity_dict.values())

    @classmethod
    def unique_by_user_utt_value(cls, entities: Iterable["Entity"]) -> List["Entity"]:
        """
        Given a list of entities, return unique entities by its user utterance values.
        If there are multiple entities of the same user utterance value, single out the
        one with the highest score.
        """
        entity_dict = dict()
        for entity in entities:
            user_utt_value, score = entity.user_utt_value, entity.score
            if (
                user_utt_value not in entity_dict
                or entity_dict[user_utt_value].score < score
            ):
                entity_dict[user_utt_value] = entity
        return list(entity_dict.values())


class StringEntity(Entity):
    """ entity type of string """

    value_types = str

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "StringEntity":
        """
        Default extraction method. We assume that the NER classifier returns
        the following dictionary
        {
            'label': 'SOME_LABEL',
            'token': 'some_string',
            'probability': some_float
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            label=ner_model_output["label"],
            span=ner_model_output["span"],
        )

    @classmethod
    def from_spelling(cls, utterance: str) -> List["StringEntity"]:
        """
        Default extraction method. Just merge tokens w/o spaces
        """
        return [cls(1, ExtractionMethod.SPELLING, utterance.replace(" ", ""))]


class DateEntity(StringEntity):
    """Entity class for the 'DATE' NER label from the OntoNotes dataset. This
    label includes 'absolute or relative dates or periods'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "DateEntity":
        """
        dictionary of the form:
        {
            'label': 'DATE',
            'probability': 0.99196035,
            'token': '3/14/15',
            "normalizedValue": "2015-03-14T00:00:00.000Z", # this is optional
            'span': {'end': 7}
        }
        """
        normalized_value = None
        if "normalizedValue" in ner_model_output:
            normalized_value = cls.normalize_value(ner_model_output["normalizedValue"])
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    def display_value(self) -> str:
        """Converts the normalized Date object into a ISO 8601 Date format string."""
        if self.normalized_value:
            return self.normalized_value.strftime("%B %-d, %Y")
        else:
            return self.value

    @staticmethod
    def normalize_value(value: str) -> date:
        """Normalizes a string in the ISO 8601 format into a Date object."""
        extracted_date, extracted_time = value.split("T")
        return date.fromisoformat(extracted_date)


class EmailEntity(StringEntity):
    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "EmailEntity":
        """
        dictionary of the form:
        {
            'label': 'DUCKLING/email',
            'token': 'peter@hotmail.com',
            'normalizedValue': 'peter@hotmail.com'
        }
        """
        return cls(
            score=1,
            method=ExtractionMethod.NER,
            user_utt_value=ner_model_output["normalizedValue"],
            span=ner_model_output["span"] if "span" in ner_model_output else None,
        )

    @classmethod
    def from_spelling(cls, utterance: str) -> List["EmailEntity"]:
        """
        Extract email from the given utterance
        We assume utterance is either
            1. not a valid email address, in which case None is returned
            2. a valid email address, with no filler words
                (i.e., it's, it is, my email is, ...)
        """
        words = utterance.split()
        res = re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z0-9.\-_]+[a-zA-Z0-9]", utterance)
        if res:
            # extract email addresses that are complete
            return [cls(1, ExtractionMethod.SPELLING, email) for email in res]
        else:
            # try to extract email address from utterance
            at = None
            for i in range(len(words)):
                if words[i].lower() == "at":
                    at = i
            if not at:
                return []
            words[at] = "@"
            end = at + 1
            while end + 1 < len(words):
                if (
                    words[end].lower() == "dot"
                    or words[end] == "."
                    and words[end + 1].lower() == "com"
                ):
                    words[end] = "."
                    words[end + 1] = "com"
                    end = end + 1
                    break
                end += 1
            if end == len(words):
                return []
            first_half = "".join(words[:at])
            second_half = "".join(words[at : end + 1])
            res = first_half + second_half
            return [cls(1, ExtractionMethod.SPELLING, res.replace(" ", ""))]


class EventEntity(StringEntity):
    """Entity class for the 'EVENT' NER label from the OntoNotes dataset. This label
    includes 'named hurricanes, battles, wars, sports events, etc.'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "EventEntity":
        """
        dictionary of the form:
        {
            'label': 'EVENT',
            'probability': 0.99196035,
            'token': 'Hurricane Katrina',
            'span': {'end': 17}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class FacilityEntity(StringEntity):
    """Entity class for the 'FAC' NER label from the OntoNotes dataset. This
    label includes 'buildings, airports, highways, bridges, etc.'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "FacilityEntity":
        """
        dictionary of the form:
        {
            'label': 'FAC',
            'probability': 0.99196035,
            'token': 'Golden Gate Bridge',
            'span': {'end': 18}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class LanguageEntity(StringEntity):
    """Entity class for the 'LANGUAGE' NER label from the OntoNotes dataset. This
    label includes 'any named language'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "LanguageEntity":
        """
        dictionary of the form:
        {
            'label': 'LANGUAGE',
            'probability': 0.99196035,
            'token': 'Spanish',
            'span': {'end': 7}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class LawEntity(StringEntity):
    """Entity class for the 'LAW' NER label from the OntoNotes dataset. This
    label includes 'named documents made into laws'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "LawEntity":
        """
        dictionary of the form:
        {
            'label': 'LAW',
            'probability': 0.99196035,
            'token': 'Civil Rights Act of 1964',
            'span': {'end': 24}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class LocationEntity(StringEntity):
    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "LocationEntity":
        """
        dictionary of the form:
        {
            'label': 'LOC',
            'probability': 0.99196035,
            'token': 'san francisco',
            'span': {'end': 13}
        }
        """
        normalized_value = None
        if "normalizedValue" in ner_model_output:
            items = ner_model_output["normalizedValue"].split("|")
            normalized_value = {}
            for item in items:
                key, value = item.split(":")
                normalized_value[key] = value
            normalized_value = tuple(normalized_value.items())
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    def display_value(self) -> str:
        """Returns the human readable format of the value."""
        if self.normalized_value:
            address = []
            for address_key, value in self.normalized_value:
                address_key_split = re.findall("[A-Z][^A-Z]*", address_key)
                address.append(f"{' '.join(address_key_split)}: {value}")
            return "\n".join(address)
        return str(self.user_utt_value)


class MoneyEntity(StringEntity):
    """Entity class for the 'MONEY' NER label from the OntoNotes dataset. This
    label includes 'monetary values, including unit'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "MoneyEntity":
        """
        Extract money from the user utterance.

        dictionary of the form:
        {
            'label': 'MONEY',
            'probability': 0.99196035,
            'token': '$500',
            'normalizedValue': 'value:500|unit:$' # this field is optional
            'span': {'end': 4}
        }
        """
        normalized_value = None
        if "normalizedValue" in ner_model_output:
            items = ner_model_output["normalizedValue"].split("|")
            normalized_value = {}
            for item in items:
                key, value = item.split(":")
                if key == "value":
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                normalized_value[key] = value
            normalized_value = tuple(normalized_value.items())
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    def display_value(self) -> str:
        """Returns the human readable format of the value.

        This method formats dollars with commas after every 3 digits and two digits
        after the decimal point. For currencies that are not dollars, this method
        returns the quantity followed by the the monetary unit, for example, 3 EUR.

        Here are the currencies supported by Duckling (normalization method
        that is supported by default) in English:
        https://github.com/facebookarchive/duckling_old/blob/master/resources/languages/en/rules/finance.clj
        """
        if self.normalized_value:
            normalized_value = dict(self.normalized_value)
            monetary_unit = normalized_value["unit"]
            value = normalized_value["value"]
            if monetary_unit == "cent":
                value *= 0.01
                monetary_unit = "$"
            if monetary_unit == "$":
                # This is to format dollars in the US.
                return f"${value:,.2f}"
            return f"{value} {monetary_unit}"
        return str(self.user_utt_value)


class NORPEntity(StringEntity):
    """Entity class for the 'NORP' NER label from the OntoNotes dataset. This
    label includes 'nationalities or religious or political groups'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "NORPEntity":
        """
        dictionary of the form:
        {
            'label': 'NORP',
            'probability': 0.99196035,
            'token': 'Buddhists',
            'span': {'end': 9}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class OrdinalEntity(StringEntity):
    """Entity class for the 'ORDINAL' NER label from the OntoNotes dataset. This
    label includes '"first", "second"'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "OrdinalEntity":
        """
        dictionary of the form:
        {
            'label': 'ORDINAL',
            'probability': 0.99196035,
            'token': '1st',
            'span': {'end': 3}
        }
        """
        normalized_value = None
        if "normalizedValue" in ner_model_output:
            try:
                normalized_value = int(ner_model_output["normalizedValue"])
            except ValueError:
                pass
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    def display_value(self) -> str:
        """Returns the human readable format of the value."""
        if self.normalized_value:
            return num2words(self.normalized_value, to="ordinal")
        return str(self.user_utt_value)


class OrganizationEntity(StringEntity):
    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "OrganizationEntity":
        """
        dictionary of the form:
        {
            'label': 'ORG',
            'probability': 0.99196035,
            'token': 'hulu',
            'span': {'end': 4}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class PercentEntity(StringEntity):
    """Entity class for the 'PERCENT' NER label from the OntoNotes dataset. This
    label includes 'percentage (including "%")'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "PercentEntity":
        """
        dictionary of the form:
        {
            'label': 'PERCENT',
            'probability': 0.99196035,
            'token': '90%',
            'span': {'end': 3}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class PersonEntity(StringEntity):
    """Entity class for the 'PERSON' NER label for the OntoNotes dataset."""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "PersonEntity":
        """
        dictionary of the form:
        {
            'label': 'PERSON',
            'probability': 0.99196035,
            'token': 'Albert Einstein',
            'span': {'end': 15}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class PhoneNumberEntity(StringEntity):
    """Entity class for the 'phone-number' Duckling label."""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "PhoneNumberEntity":
        """
        dictionary of the form:
        {
            'label': 'DUCKLING/phone-number',
            'token': '+1 (650) 123-4567',
            'normalizedValue': '(+1) 6501234567'
        }
        """
        return cls(
            score=1,
            method=ExtractionMethod.NER,
            user_utt_value=ner_model_output["token"],
            normalized_value=ner_model_output["normalizedValue"],
            span=ner_model_output["span"],
        )


class PickListEntity(StringEntity):
    """
    Entity type of Pick List
    Entity value is extracted by FuzzyMatchingEntityExtractor
    """

    pass


class ProductEntity(StringEntity):
    """Entity class for the 'PRODUCT' NER label from the OntoNotes dataset. This
    label includes 'vehicles, weapons, foods, etc. (Not services)'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "ProductEntity":
        """
        dictionary of the form:
        {
            'label': 'PRODUCT',
            'probability': 0.99196035,
            'token': 'iPhone',
            'span': {'end': 6}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class QuantityEntity(StringEntity):
    """Entity class for the 'QUANTITY' NER label from the OntoNotes dataset. This
    label includes 'measurements, as of weight or distance'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "QuantityEntity":
        """
        dictionary of the form:
        {
            'label': 'QUANTITY',
            'probability': 0.99196035,
            'token': '5 feet',
            'span': {'end': 6}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class TimeEntity(StringEntity):
    """Entity class for the 'TIME' NER label from the OntoNotes dataset. This
    label includes 'times smaller than a day'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "TimeEntity":
        """
        dictionary of the form:
        {
            "label": "TIME",
            "probability": 0.9826260805130005,
            "token": "1 p.m.",
            "normalizedValue": "2021-01-15T13:00:00.000Z", # this is optional
            "span": {"end": 6},
        },
        """
        normalized_value = None
        if "normalizedValue" in ner_model_output:
            normalized_value = cls.normalize_value(ner_model_output["normalizedValue"])
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    @staticmethod
    def normalize_value(value: str) -> time:
        """Normalizes a string of the ISO 8601 Time format into a Time object."""
        extracted_date, extracted_time = value.split("T")
        if extracted_time[-1] == "Z":
            extracted_time = extracted_time[:-1]
        return time.fromisoformat(extracted_time)


class URLEntity(StringEntity):
    """Entity class for the URL Duckling entity (`DUCKLING/url` label)."""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "URLEntity":
        """
        dictionary of the form:
        {
            "label": "DUCKLING/url",
            "token": "npr.org",
            "normalizedValue": "npr.org",
            "span": {"end": 7},
        },
        """
        return cls(
            1,
            ExtractionMethod.NER,
            ner_model_output["token"],
            normalized_value=ner_model_output["normalizedValue"],
            span=ner_model_output["span"],
        )


class UserUttEntity(StringEntity):
    """
    entity type of User Utterance
    some entity APIs may need the whole user utterance as input
    """

    @classmethod
    def from_original_user_utt(cls, utterance: str) -> List["UserUttEntity"]:
        """
        Return user utterance directly for 3rd party APIs

        This is not a required method that needs to be implemented for each type of
        entity. UserUttExtractor.extract will call this method
        """
        return [cls(1, ExtractionMethod.USER_UTTERANCE, utterance)]


class WorkOfArtEntity(StringEntity):
    """Entity class for the 'WORK_OF_ART' NER label from the OntoNotes dataset. This
    label includes 'titles of books, songs, etc.'"""

    @classmethod
    def from_ner_model(cls, ner_model_output: dict) -> "WorkOfArtEntity":
        """
        dictionary of the form:
        {
            'label': 'WORK_OF_ART',
            'probability': 0.99196035,
            'token': 'I Loves You, Porgy',
            'span': {'end': 18}
        }
        """
        return cls(
            ner_model_output["probability"],
            ExtractionMethod.NER,
            ner_model_output["token"],
            span=ner_model_output["span"],
        )


class ZipCodeEntity(StringEntity):
    """
    This entity class represents a US zipcode. Every instance must have a valid
    string value that matches `zip_re` regex condition. Within `from_ner_model` and
    `from_spelling` methods, if the value is not a valid zip code, it shall not
    create this instance.

    This class inherits from StringEntity because a zipcode can start with 0, so it is
    more convenient to store the zip code as a string rather than integer

    Attributes:
        zip_re: simple regex to tell if the zip code is valid; 00000 - 99999
            (not exact; just an easy check)
    """

    zip_re = re.compile("^[0-9]{5}$")

    @classmethod
    def from_ner_model(cls, ner_model_output: dict):
        """
        dictionary of the form:
        {
            'label': 'CARDINAL',
            'probability': 0.99196035,
            'token': '06101',
            'span': {'end': 5}
        }
        """
        zipcode = ner_model_output["token"].replace(" ", "")
        if cls.zip_re.match(zipcode):
            # create this instance only when it is a valid zip code
            return cls(
                score=ner_model_output["probability"],
                method=ExtractionMethod.NER,
                user_utt_value=zipcode,
                span=ner_model_output["span"],
            )
        else:
            return None

    @classmethod
    def from_spelling(cls, utterance: str) -> List["StringEntity"]:
        entities = super().from_spelling(utterance)
        valid_entities = []
        for entity in entities:
            zipcode = entity.value
            if cls.zip_re.match(zipcode):
                # create this instance only when it is a valid zip code
                valid_entities.append(entity)
        return valid_entities


class NumberEntity(Entity):
    """ entity type for integers and floating point numbers """

    value_types = (int, float)


class CardinalEntity(NumberEntity):
    @classmethod
    def from_ner_model(cls, ner_model_output: dict):
        """
        dictionary of the form:
        {
            'label': 'CARDINAL',
            'probability': 0.99196035,
            'token': '94301',
            "normalizedValue": "94301", # this is optional
            'span': {'end': 5}
        }
        """
        has_number_value = True
        try:
            value = float(ner_model_output["token"])
        except ValueError:
            # token may have spaces in between
            try:
                value = float(ner_model_output["token"].replace(" ", ""))
            except ValueError:
                has_number_value = False
                value = ner_model_output["token"]
        if isinstance(value, float) and int(value) == value:
            value = int(value)

        normalized_value = None
        if "normalizedValue" in ner_model_output:
            try:
                normalized_value = float(ner_model_output["normalizedValue"])
                if (
                    isinstance(normalized_value, float)
                    and int(normalized_value) == normalized_value
                ):
                    normalized_value = int(normalized_value)
                has_number_value = True
            except ValueError:
                has_number_value = False
        if not has_number_value:
            return None
        score = 1
        if "probability" in ner_model_output:
            score = ner_model_output["probability"]

        return cls(
            score=score,
            method=ExtractionMethod.NER,
            user_utt_value=value,
            normalized_value=normalized_value,
            span=ner_model_output["span"],
        )

    @classmethod
    def from_spelling(cls, utterance: str) -> List["CardinalEntity"]:
        """
        Merge consecutive digit characters into one Entity
        """
        tokens = utterance.split()
        result = []
        digit_token = ""
        for token in tokens:
            if token.isdigit():
                digit_token += token
            elif digit_token:
                result.append(digit_token)
                digit_token = ""
        if digit_token:
            result.append(digit_token)
        return [cls(1, ExtractionMethod.SPELLING, int(digit)) for digit in result]


class EntityExtractor(object):
    """
    Generic entity extractor class. Every entity extraction method must
    subclass this and provide extract method

    The object should be instantiated with any external variable necessary for
    extracting the entity other than the raw utterance itself
    """

    def extract(self, utterance: str):
        """
        extract a list of entities
        """
        raise NotImplementedError


class UserUttExtractor(EntityExtractor):
    def extract(self, utterance: str) -> List[UserUttEntity]:
        """
        Return user utterance directly as extracted results.
        """
        return UserUttEntity.from_original_user_utt(utterance)


class NamedEntityExtractor(EntityExtractor):
    """
    Attributes:
        label2type (dict): NER server label to entity types mapping. Will return the
            first successful entity type in the list
    """

    label2type = {
        "CARDINAL": [ZipCodeEntity, CardinalEntity],
        "DATE": [DateEntity],
        "DUCKLING/email": [EmailEntity],
        "EMAIL": [EmailEntity],
        "EVENT": [EventEntity],
        "FAC": [FacilityEntity],
        "LANGUAGE": [LanguageEntity],
        "LAW": [LawEntity],
        "GPE": [LocationEntity],
        "LOC": [LocationEntity],
        "AP/LOCATION": [ZipCodeEntity, LocationEntity],
        "MONEY": [MoneyEntity],
        "NORP": [NORPEntity],
        "DUCKLING/number": [ZipCodeEntity, CardinalEntity],
        "ORDINAL": [OrdinalEntity],
        "ORG": [OrganizationEntity],
        "PERCENT": [PercentEntity],
        "PERSON": [PersonEntity],
        "DUCKLING/phone-number": [PhoneNumberEntity],
        "PRODUCT": [ProductEntity],
        "QUANTITY": [QuantityEntity],
        "TIME": [TimeEntity],
        "DUCKLING/url": [URLEntity],
        "WORK_OF_ART": [WorkOfArtEntity],
    }
    # A dictionary of labels that map from a label to a label of the normalized entity
    label2normalized_label = {
        "DATE": "DUCKLING/time",
        "TIME": "DUCKLING/time",
        "CARDINAL": "DUCKLING/number",
        "ORDINAL": "DUCKLING/ordinal",
        "MONEY": "DUCKLING/amount-of-money",
    }
    # A set of labels for normalized entities
    normalized_labels = set(label2normalized_label.values())

    def __init__(self, ner_model_output: dict):
        self.model_output = ner_model_output.copy()

    def match_normalized_values(self, candidates):
        """Copies the normalized values from the candidates from DUCKLING to the
        candidates of standard NER labels and returns a new list of candidates where
        the used DUCKLING labels are filtered out."""
        normalized_candidates = []
        value_to_candidates = {}
        for candidate in candidates:
            if candidate["label"] in self.normalized_labels:
                normalized_candidates.append(candidate)
            else:
                value = candidate["token"]
                if value not in value_to_candidates:
                    value_to_candidates[value] = []
                value_to_candidates[value].append(candidate)
        if not normalized_candidates:
            return candidates
        for normalized_candidate in normalized_candidates:
            value = normalized_candidate["token"]
            normalized_value = normalized_candidate["normalizedValue"]
            normalized_label = normalized_candidate["label"]
            if value in value_to_candidates:
                for candidate in value_to_candidates[value]:
                    label = candidate["label"]
                    if (
                        label in self.label2normalized_label
                        and self.label2normalized_label[label] == normalized_label
                    ):
                        candidate["normalizedValue"] = normalized_value
        new_candidates = []
        for candidates in value_to_candidates.values():
            new_candidates.extend(candidates)
        return new_candidates

    def extract(self, utterance: str) -> List[Entity]:
        """
        extract all possible entities from the ner model output
        utterance is not used

        Each NER candidate from the model_output is used to create an entity by
        instantiating via each entity's from_ner_model class-method
        """
        result = []
        if "probabilities" in self.model_output:
            candidates = self.match_normalized_values(
                self.model_output["probabilities"]
            )
            for candidate_dict in candidates:
                entity = None
                if candidate_dict["label"] in self.label2type:
                    for entity_type in self.label2type[candidate_dict["label"]]:
                        entity = entity_type.from_ner_model(candidate_dict)
                        if entity is not None:
                            break  # we stop when we obtain the first valid entity
                else:
                    # fall back to StringEntity
                    try:
                        entity = StringEntity.from_ner_model(candidate_dict)
                    except KeyError:
                        entity = None
                if entity is not None:
                    # can return None if there is an error
                    result.append(entity)
        return result


class SpellingEntityExtractor(EntityExtractor):
    """
    It requires the expected type of the entity
    """

    def __init__(self, entity_type: type(Entity)):
        self.entity_type = entity_type

    def extract(self, utterance: str) -> List[Entity]:
        """
        Clean up the text and feed into each Entity's from_spelling constructor
        for appropriate extraction
        """
        utterance = self._clean_up_text(utterance)
        entities = self.entity_type.from_spelling(utterance)
        return entities

    @classmethod
    def _clean_up_text(cls, utterance: str):
        """
        preforms the following

        find the starting point using rule-based and discard initial words that
        are not meaningful
            ex) "so, it's is salesforce" --> "salesforce"

        clean up spelling using rule-based
            ex) "a as in apple, b as in ball, y as in yellow" --> "a b y"
        """

        start_set = {"yes", "no", "so"}
        punctuations = ",!?"  # to be removed

        # remove punctuations TODO: do it with regex?
        for p in punctuations:
            utterance = utterance.replace(p, "")

        tokens = utterance.split()

        if "is" in tokens:
            i = tokens.index("is") + 1
        elif "it's" in tokens:
            i = tokens.index("it's") + 1
        elif tokens[0] in start_set:
            i = 1
        else:
            i = 0

        idx = i
        while idx < len(tokens) - 3:

            tok_char = tokens[idx]
            tok_as = tokens[idx + 1]
            tok_in = tokens[idx + 2]
            tok_example = tokens[idx + 3]

            # a series of conditional checks
            if (
                tok_as == "as"
                and tok_in == "in"
                and len(tok_char) == 1
                and tok_char in "abcdefghijklmnopqrstuvwxyz"
                and tok_example[0] == tok_char
            ):

                # now, it must be in the form "a as in apple",
                # where idx points to "as". Remove "as in apple"
                tokens[idx + 1] = tokens[idx + 2] = tokens[idx + 3] = ""
                # skip 3 tokens
                idx += 4
            else:
                tokens[idx] = tokens[idx]
                idx += 1

        value = " ".join(tokens[i:])
        return re.sub(" +", " ", value)


class FuzzyMatchingEntityExtractor(EntityExtractor):
    """
    Fuzzy matching one of the candidates
    """

    def __init__(self, candidates: List[str]):
        # every candidate must be of string
        self.candidates = [str(c) for c in candidates]

    def extract(self, utterance: str) -> List[PickListEntity]:
        """
        Fuzzy logic matching returns a StringEntity
        """
        res = process.extract(utterance, self.candidates, limit=1, scorer=fuzz.ratio)
        entity = PickListEntity(
            res[0][1] / 100.0, ExtractionMethod.FUZZY_LOGIC, res[0][0]
        )
        return [entity] if entity else []


class RegexMatchingEntityExtractor(EntityExtractor):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def extract(self, utterance: str) -> List[StringEntity]:
        """
        Regex matching returns a list of StringEntities
        """
        res = re.findall(self.pattern, utterance)
        return [StringEntity(1, ExtractionMethod.REGEX, value) for value in res]


def extract_value_from_entity(value) -> Any:
    """Extracts the value from value if the value is an entity. We need this
    function because the entity in the dialogue state manager and dialogue tree can be
    a string or an entity.
    """
    if isinstance(value, Entity):
        value = value.value
    return value


def extract_display_value_from_entity(value) -> str:
    """Extracts the display value from value if the value is an entity. We need this
    function because the entity in the dialogue state manager and dialogue tree can be
    a string or an entity.
    """
    display_value = str(value)
    if isinstance(value, Entity):
        display_value = value.display_value()
    return display_value


if __name__ == "__main__":
    entity1 = StringEntity(0.95, ExtractionMethod.NER, "some string")
    entity2 = StringEntity(0.95, ExtractionMethod.NER, "some string")
    assert entity1 == entity2

    entity3 = StringEntity(0.95, ExtractionMethod.SPELLING, "some string")
    assert entity1 != entity3

    ner_model = NER("34.122.137.192:50051")
    utt = (
        "Albert Einstein's email address is einstein@albert.io;"
        " his zip code is 94301"
    )
    model_output = ner_model(utt, returnSpan=True)
    print(NamedEntityExtractor(model_output).extract(utt))

    utt = (
        "it's k as in king, i as in ice, n as in nice, g as in game, "
        "s as in sun, i as in idle, at hot mail dot com"
    )
    print(SpellingEntityExtractor(EmailEntity).extract(utt))

    utt = "pet e r at hotmail dot com"
    print(SpellingEntityExtractor(EmailEntity).extract(utt))

    utt = "a as in apple, b as in boy, b as in boy, y as in yellow"
    print(SpellingEntityExtractor(PersonEntity).extract(utt))

    utt = "my zipcode is 9 4 3 2 9"
    print(SpellingEntityExtractor(CardinalEntity).extract(utt))

    utt = "9 4 3 2 9"
    print(SpellingEntityExtractor(CardinalEntity).extract(utt))

    utt = "my zipcode is 9 4 3 2 9"
    print(SpellingEntityExtractor(EmailEntity).extract(utt))

    utt = "i live in san francisco"
    model_output = ner_model(utt, returnSpan=True)
    print(NamedEntityExtractor(model_output).extract(utt))

    utt = "my plan is hulu live but I dont know the add on"
    fuzzyExtractor = FuzzyMatchingEntityExtractor(["live_tv", "hulu_tv", "hulu_live"])
    print(fuzzyExtractor.extract(utt))

    utt = "king s i at salesforce dot com"
    print(fuzzyExtractor.extract(utt))

    utt = "my plan is hulu live and my username is Tony"
    model_output = ner_model(utt, returnSpan=True)
    print(NamedEntityExtractor(model_output).extract(utt))

    utt = "zip number is 94301 and 33221"
    regexExtractor = RegexMatchingEntityExtractor(r"\d{5}")
    print(regexExtractor.extract(utt))

    utt = "how many people are working at salesforce"
    user_uttExtractor = UserUttExtractor()
    spellingExtractor = SpellingEntityExtractor(StringEntity)
    print(spellingExtractor.extract(utt))
    print(user_uttExtractor.extract(utt))
