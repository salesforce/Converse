# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from datetime import date, time
import unittest

from Converse.entity.entity import (
    # Entity classes
    CardinalEntity,
    DateEntity,
    EmailEntity,
    EventEntity,
    FacilityEntity,
    LanguageEntity,
    LawEntity,
    LocationEntity,
    MoneyEntity,
    NORPEntity,
    OrdinalEntity,
    OrganizationEntity,
    PercentEntity,
    PersonEntity,
    PhoneNumberEntity,
    ProductEntity,
    QuantityEntity,
    TimeEntity,
    URLEntity,
    WorkOfArtEntity,
    ZipCodeEntity,
    # Entity extractors
    FuzzyMatchingEntityExtractor,
    NamedEntityExtractor,
    RegexMatchingEntityExtractor,
    SpellingEntityExtractor,
    UserUttExtractor,
)


class TestSpellingExtractor(unittest.TestCase):
    def setUp(self):
        self.email_extractor = SpellingEntityExtractor(EmailEntity)
        self.cardinal_extractor = SpellingEntityExtractor(CardinalEntity)
        self.person_extractor = SpellingEntityExtractor(PersonEntity)
        self.zipcode_extractor = SpellingEntityExtractor(ZipCodeEntity)

    def test_email_extraction(self):
        utt = "pet e r at hotmail dot com"
        res = self.email_extractor.extract(utt)
        self.assertEqual(res[0].value, "peter@hotmail.com")

    def test_wrong_type_extraction1(self):
        utt = "my zipcode is 9 4 3 2 9"
        res = self.email_extractor.extract(utt)
        self.assertEqual(len(res), 0)

    def test_wrong_type_extraction2(self):
        utt = "pet e r at hotmail dot com"
        res = self.cardinal_extractor.extract(utt)
        self.assertEqual(len(res), 0)

    def test_cardinal_extraction1(self):
        utt = "my zipcode is 9 4 3 2 9"
        res = self.cardinal_extractor.extract(utt)
        self.assertEqual(res[0].value, 94329)

    def test_cardinal_extraction2(self):
        utt = "9 4 3 2 9"
        res = self.cardinal_extractor.extract(utt)
        self.assertEqual(res[0].value, 94329)

    def test_name_extraction(self):
        utt = "a as in apple, b as in boy, b as in boy, y as in yellow"
        res = self.person_extractor.extract(utt)
        self.assertEqual(res[0].value, "abby")

    def test_valid_zipcode_extraction(self):
        utt = "9 4 3 0 1"
        res = self.zipcode_extractor.extract(utt)
        self.assertEqual(res[0].value, "94301")

    def test_invalid_zipcode_extraction(self):
        utt = "9 4 3 0 1 2"
        res = self.zipcode_extractor.extract(utt)
        self.assertEqual(res, [])


class TestRegexExtractor(unittest.TestCase):
    def setUp(self):
        self.zip_extractor = RegexMatchingEntityExtractor(r"\d{5}")

    def test_zip_code_that_matches(self):
        resp1 = ["94301", "33221"]
        utt = "zip number is 94301 and 33221"
        res = self.zip_extractor.extract(utt)
        for entity, target in zip(res, resp1):
            self.assertEqual(entity.value, target)

    def test_zip_code_that_does_not_match(self):
        utt = "pet e r at hotmail dot com"
        res = self.zip_extractor.extract(utt)
        self.assertEqual(len(res), 0)


class TestFuzzyExtractor(unittest.TestCase):
    def setUp(self):
        self.fuzzy_entity_extractor = FuzzyMatchingEntityExtractor(
            ["live_tv", "hulu_tv", "hulu_live", "A", "AAPL", "AA"]
        )

    def test_likely_match(self):
        utt = "my plan is hulu live but I dont know the add on"
        res = self.fuzzy_entity_extractor.extract(utt)
        self.assertEqual(res[0].value, "hulu_live")

    def test_unlikely_match(self):
        utt = "pet e r at hotmail dot com"
        res = self.fuzzy_entity_extractor.extract(utt)
        self.assertEqual(res[0].value, "AAPL")

    def test_exact_match(self):
        utt = "yes, AAPL"
        res = self.fuzzy_entity_extractor.extract(utt)
        self.assertEqual(res[0].value, "AAPL")


class TestUserUttExtractor(unittest.TestCase):
    def setUp(self):
        self.user_utt_extractor = UserUttExtractor()

    def test_user_utt(self):
        utt = "my plan is hulu live but I dont know the add on"
        res = self.user_utt_extractor.extract(utt)
        self.assertEqual(res[0].value, utt)

        utt = "pet e r at Hotmail dot com"
        res = self.user_utt_extractor.extract(utt)
        self.assertEqual(res[0].value, utt)


class TestNamedEntityExtractor(unittest.TestCase):
    def setUp(self):
        info1 = {"ner": {"success": True}}

        info2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.8929017186164856,
                        "token": "9 4 3",
                        "span": {"start": 14, "end": 19},
                    },
                    {
                        "label": "CARDINAL",
                        "probability": 0.809390664100647,
                        "token": "9",
                        "span": {"start": 22, "end": 23},
                    },
                ],
            },
            "negation": (
                ["my", "zipcode", "is", "9", "4", "3", "2", "9"],
                [(-1, -1, -1)],
            ),
            "coref": {},
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }

        info3 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.38835767,
                        "token": "k",
                        "span": {"end": 1},
                    }
                ],
            },
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "negation": {
                "wordlist": [
                    "k",
                    "i",
                    "n",
                    "g",
                    "s",
                    "i",
                    "at",
                    "salesforce",
                    "dot",
                    "com",
                ],
                "triplets": [(-1, -1, -1)],
            },
            "coref": {
                "words": [
                    "k",
                    "i",
                    "n",
                    "g",
                    "s",
                    "i",
                    "at",
                    "salesforce",
                    "dot",
                    "com",
                ],
                "predicted_clusters": [],
                "top_spans": [(1, 4), (1, 5), (5, 6), (7, 10)],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }

        info4 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.8583359,
                        "token": "94301",
                        "span": {"start": 15, "end": 20},
                    },
                    {
                        "label": "AP/LOCATION",
                        "probability": 0.9523145,
                        "token": "94301",
                        "normalizedValue": "ZipCode:94301",
                        "span": {"start": 15, "end": 20},
                    },
                ],
            },
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "negation": {
                "wordlist": ["my", "zip", "code", "is", "94301"],
                "triplets": [(-1, -1, -1)],
            },
            "coref": {
                "words": ["my", "zip", "code", "is", "94301"],
                "predicted_clusters": [],
                "top_spans": [(0, 1), (0, 3)],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }

        self.named_entity_extractor1 = NamedEntityExtractor(info1["ner"])
        self.named_entity_extractor2 = NamedEntityExtractor(info2["ner"])
        self.named_entity_extractor3 = NamedEntityExtractor(info3["ner"])
        self.named_entity_extractor4 = NamedEntityExtractor(info4["ner"])

    def test_ner_with_no_candidate(self):
        utt = "I don't know my zipcode"
        res = self.named_entity_extractor1.extract(utt)
        self.assertEqual(len(res), 0)

    def test_ner_with_candidates(self):
        resp2 = [943, 9]
        utt = "my zipcode is 94301"
        res = self.named_entity_extractor2.extract(utt)
        for entity, target in zip(res, resp2):
            self.assertEqual(entity.value, target)

    def test_ner_exception(self):
        utt = "k i n g s i at salesforce dot com"
        res = self.named_entity_extractor3.extract(utt)
        self.assertEqual(res, [])

    def check_ner_info(
        self,
        ner_info,
        user_utterance,
        expected_types,
        expected_values,
        expected_user_utt_values=None,
        expected_display_values=None,
    ):
        named_entity_extractor = NamedEntityExtractor(ner_info)
        res = named_entity_extractor.extract(user_utterance)
        self.assertEqual(len(res), len(expected_values))
        for entity, expected_type, expected_value in zip(
            res, expected_types, expected_values
        ):
            self.assertTrue(isinstance(entity, expected_type))
            self.assertEqual(entity.value, expected_value)
        if expected_display_values:
            for entity, expected_user_utt_value, expected_display_value in zip(
                res, expected_user_utt_values, expected_display_values
            ):
                self.assertEqual(entity.user_utt_value, expected_user_utt_value)
                self.assertEqual(entity.display_value(), expected_display_value)

    def test_address(self):
        """Tests that the values are extracted properly from the address parser."""
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/number",
                    "token": "123",
                    "normalizedValue": "123.0",
                    "span": {"start": 14, "end": 17},
                },
                {
                    "label": "DUCKLING/number",
                    "token": "94020",
                    "normalizedValue": "94020.0",
                    "span": {"start": 45, "end": 50},
                },
                {
                    "label": "CARDINAL",
                    "probability": 0.4174571633338928,
                    "token": "123",
                    "span": {"start": 14, "end": 17},
                },
                {
                    "label": "FAC",
                    "probability": 0.15432994067668915,
                    "token": "Main Street,",
                    "span": {"start": 18, "end": 30},
                },
                {
                    "label": "LOC",
                    "probability": 0.7884138822555542,
                    "token": "Palo Alto, CA",
                    "span": {"start": 31, "end": 44},
                },
                {
                    "label": "DATE",
                    "probability": 0.12766370177268982,
                    "token": "94020",
                    "span": {"start": 45, "end": 50},
                },
                {
                    "label": "AP/LOCATION",
                    "probability": 0.9999514818191528,
                    "token": "123 Main Street, Palo Alto, CA 94020",
                    "normalizedValue": (
                        "AddressNumber:123|StreetName:Main|"
                        "StreetNamePostType:Street,|PlaceName:Palo Alto,|StateName:CA"
                        "|ZipCode:94020"
                    ),
                    "span": {"start": 14, "end": 50},
                },
            ],
        }
        user_utterance = "My address is 123 Main Street, Palo Alto, CA 94020"
        expected_types = [
            CardinalEntity,
            FacilityEntity,
            LocationEntity,
            DateEntity,
            LocationEntity,
        ]
        expected_values = [
            123,
            "Main Street,",
            "Palo Alto, CA",
            "94020",
            (
                ("AddressNumber", "123"),
                ("StreetName", "Main"),
                ("StreetNamePostType", "Street,"),
                ("PlaceName", "Palo Alto,"),
                ("StateName", "CA"),
                ("ZipCode", "94020"),
            ),
        ]
        expected_user_utt_values = [
            123,
            "Main Street,",
            "Palo Alto, CA",
            "94020",
            "123 Main Street, Palo Alto, CA 94020",
        ]
        expected_display_values = [
            "123",
            "Main Street,",
            "Palo Alto, CA",
            "94020",
            (
                "Address Number: 123\n"
                "Street Name: Main\n"
                "Street Name Post Type: Street,\n"
                "Place Name: Palo Alto,\n"
                "State Name: CA\n"
                "Zip Code: 94020"
            ),
        ]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_cardinal_spelled_out_with_words(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "CARDINAL",
                    "probability": 0.5632068514823914,
                    "token": "eighty eight",
                    "span": {"start": 7, "end": 19},
                },
                {
                    "label": "DUCKLING/number",
                    "token": "eighty eight",
                    "normalizedValue": "88",
                },
            ],
        }
        user_utterance = "I want eighty eight hugs"
        expected_types = [CardinalEntity]
        expected_values = [88]
        expected_user_utt_values = ["eighty eight"]
        expected_display_values = ["88"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_cardinal_spelled_out_with_words_without_duckling_normalization(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "CARDINAL",
                    "token": "eighty eight",
                    "span": {"start": 7, "end": 19},
                },
            ],
        }
        user_utterance = "I want eighty eight hugs"
        expected_types = []
        expected_values = []
        expected_user_utt_values = []
        expected_display_values = []
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_cardinal_without_duckling_normalization(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "CARDINAL",
                    "probability": 0.9388434886932373,
                    "token": "34",
                    "span": {"start": 7, "end": 9},
                },
            ],
        }
        user_utterance = "I want 34 chocolates"
        expected_types = [CardinalEntity]
        expected_values = [34]
        expected_user_utt_values = [34]
        expected_display_values = ["34"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_date(self):
        """We only expect one date entity because the NamedEntityExtractor combines the
        two NER outputs into a single entity.
        """
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/time",
                    "token": "3/4/15",
                    "normalizedValue": "2015-03-04T00:00:00.000Z",
                },
                {
                    "label": "DATE",
                    "probability": 0.9402269721031189,
                    "token": "3/4/15",
                    "span": {"end": 7},
                },
            ],
        }
        user_utterance = "3/4/15"
        expected_types = [DateEntity]
        expected_values = [date(2015, 3, 4)]
        expected_user_utt_values = ["3/4/15"]
        expected_display_values = ["March 4, 2015"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_date_without_duckling(self):
        """Tests that a DateEntity is still created if there is no Duckling label."""
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DATE",
                    "probability": 0.9402269721031189,
                    "token": "3/4/15",
                    "span": {"end": 7},
                },
            ],
        }
        user_utterance = "3/4/15"
        expected_types = [DateEntity]
        expected_values = ["3/4/15"]
        expected_user_utt_values = ["3/4/15"]
        expected_display_values = ["3/4/15"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_date_without_matching_label(self):
        """Checks that the detected location entity does not have a Date object
        as the normalized value even though it also uses the same token."""
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/time",
                    "token": "3/13/24",
                    "normalizedValue": "2024-03-13T00:00:00.000Z",
                },
                {
                    "label": "DATE",
                    "probability": 0.9636090397834778,
                    "token": "3/13/24",
                    "span": {"end": 7},
                },
                {
                    "label": "AP/LOCATION",
                    "probability": 0.5368542671203613,
                    "token": "3/13/24",
                    "normalizedValue": "AddressNumber:3/13/24",
                    "span": {"end": 7},
                },
            ],
        }
        user_utterance = "3/13/24"
        expected_types = [DateEntity, LocationEntity]
        expected_values = [date(2024, 3, 13), (("AddressNumber", "3/13/24"),)]
        expected_user_utt_values = ["3/13/24", "3/13/24"]
        expected_display_values = ["March 13, 2024", "Address Number: 3/13/24"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_email(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "EMAIL",
                    "token": "peter@hotmail.com",
                    "normalizedValue": "peter@hotmail.com",
                    "span": {"end": 17},
                },
                {
                    "label": "DUCKLING/email",
                    "token": "peter@hotmail.com",
                    "normalizedValue": "peter@hotmail.com",
                    "span": {"end": 17},
                },
            ],
        }
        user_utterance = "peter@hotmail.com"
        expected_types = [EmailEntity, EmailEntity]
        expected_values = ["peter@hotmail.com", "peter@hotmail.com"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_event(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "EVENT",
                    "probability": 0.99196035,
                    "token": "Hurricane Katrina",
                    "span": {"end": 17},
                }
            ],
        }
        user_utterance = "Hurricane Katrina"
        expected_types = [EventEntity]
        expected_values = ["Hurricane Katrina"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_facility(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "FAC",
                    "probability": 0.9659203886985779,
                    "token": "Golden Gate Bridge",
                    "span": {"end": 18},
                }
            ],
        }
        user_utterance = "Golden Gate Bridge"
        expected_types = [FacilityEntity]
        expected_values = ["Golden Gate Bridge"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_gpe(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "GPE",
                    "probability": 0.97431480884552,
                    "token": "China",
                    "span": {"end": 5},
                }
            ],
        }
        user_utterance = "China"
        expected_types = [LocationEntity]
        expected_values = ["China"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_language(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "LANGUAGE",
                    "probability": 0.9770963788032532,
                    "token": "Spanish",
                    "span": {"end": 7},
                }
            ],
        }
        user_utterance = "Spanish"
        expected_types = [LanguageEntity]
        expected_values = ["Spanish"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_law(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "LAW",
                    "probability": 0.95046466588974,
                    "token": "Civil Rights Act",
                    "span": {"end": 16},
                },
                {
                    "label": "LAW",
                    "probability": 0.5817853212356567,
                    "token": "1964",
                    "span": {"start": 20, "end": 24},
                },
            ],
        }
        user_utterance = "Civil Rights Act"
        expected_types = [LawEntity, LawEntity]
        expected_values = ["Civil Rights Act", "1964"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_loc(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "LOC",
                    "probability": 0.9959089756011963,
                    "token": "San Francisco",
                    "span": {"end": 13},
                },
                {
                    "label": "AP/LOCATION",
                    "probability": 0.9997629523277283,
                    "token": "San Francisco",
                    "normalizedValue": "PlaceName:San Francisco",
                    "span": {"end": 13},
                },
            ],
        }
        user_utterance = "San Francisco"
        expected_types = [LocationEntity, LocationEntity]
        expected_values = ["San Francisco", (("PlaceName", "San Francisco"),)]
        expected_user_utt_values = ["San Francisco", "San Francisco"]
        expected_display_values = ["San Francisco", "Place Name: San Francisco"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_money(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "MONEY",
                    "probability": 0.9989566802978516,
                    "token": "$500",
                    "span": {"end": 4},
                }
            ],
        }
        user_utterance = "$500"
        expected_types = [MoneyEntity]
        expected_values = ["$500"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_money_with_duckling(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "MONEY",
                    "probability": 0.9989566802978516,
                    "token": "$1000",
                    "span": {"end": 5},
                },
                {
                    "label": "DUCKLING/amount-of-money",
                    "token": "$1000",
                    "normalizedValue": "value:1000|unit:$",
                    "span": {"end": 5},
                },
            ],
        }
        user_utterance = "$1000"
        expected_types = [MoneyEntity]
        expected_values = [(("value", 1000.0), ("unit", "$"))]
        expected_user_utt_values = ["$1000"]
        expected_display_values = ["$1,000.00"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_money_with_duckling_for_cents_input(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/number",
                    "token": "20",
                    "normalizedValue": "20.0",
                    "span": {"end": 2},
                },
                {
                    "label": "DUCKLING/amount-of-money",
                    "token": "20 cents",
                    "normalizedValue": "value:20.0|unit:cent",
                    "span": {"end": 8},
                },
                {
                    "label": "MONEY",
                    "probability": 0.9976121187210083,
                    "token": "20 cents",
                    "span": {"end": 8},
                },
            ],
        }
        user_utterance = "20 cents"
        expected_types = [MoneyEntity]
        expected_values = [(("value", 20.0), ("unit", "cent"))]
        expected_user_utt_values = ["20 cents"]
        expected_display_values = ["$0.20"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_money_with_duckling_for_spelled_out_input_with_abbreviations(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/number",
                    "token": "1M",
                    "normalizedValue": "1000000.0",
                    "span": {"end": 2},
                },
                {
                    "label": "DUCKLING/amount-of-money",
                    "token": "1M dollars",
                    "normalizedValue": "value:1000000.0|unit:$",
                    "span": {"end": 10},
                },
                {
                    "label": "MONEY",
                    "probability": 0.9928754568099976,
                    "token": "1M dollars",
                    "span": {"end": 10},
                },
            ],
        }
        user_utterance = "1M dollars"
        expected_types = [MoneyEntity]
        expected_values = [(("value", 1000000.0), ("unit", "$"))]
        expected_user_utt_values = ["1M dollars"]
        expected_display_values = ["$1,000,000.00"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_norp(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "NORP",
                    "probability": 0.9875033497810364,
                    "token": "Buddhists",
                    "span": {"end": 9},
                }
            ],
        }
        user_utterance = "Buddhists"
        expected_types = [NORPEntity]
        expected_values = ["Buddhists"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_ordinal(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "ORDINAL",
                    "probability": 0.9711340069770813,
                    "token": "1st",
                    "span": {"end": 3},
                },
            ],
        }
        user_utterance = "1st"
        expected_types = [OrdinalEntity]
        expected_values = ["1st"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_ordinal_with_duckling(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "ORDINAL",
                    "probability": 0.9711340069770813,
                    "token": "1st",
                    "span": {"end": 3},
                },
                {
                    "label": "DUCKLING/ordinal",
                    "token": "1st",
                    "normalizedValue": "1",
                    "span": {"end": 3},
                },
            ],
        }
        user_utterance = "1st"
        expected_types = [OrdinalEntity]
        expected_values = [1]
        expected_user_utt_values = ["1st"]
        expected_display_values = ["first"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_organization(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "ORG",
                    "probability": 0.99196035,
                    "token": "hulu",
                    "span": {"end": 4},
                }
            ],
        }
        user_utterance = "hulu"
        expected_types = [OrganizationEntity]
        expected_values = ["hulu"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_percent(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "PERCENT",
                    "probability": 0.9984473586082458,
                    "token": "90%",
                    "span": {"end": 3},
                }
            ],
        }
        user_utterance = "90%"
        expected_types = [PercentEntity]
        expected_values = ["90%"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_person(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "PERSON",
                    "probability": 0.9992644190788269,
                    "token": "Rosa Parks",
                    "span": {"end": 10},
                }
            ],
        }
        user_utterance = "Rosa Parks"
        expected_types = [PersonEntity]
        expected_values = ["Rosa Parks"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_phone_number(self):
        """Tests that the PhoneNumberEntity is created from the 'DUCKLING/phone-number
        label."""
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/phone-number",
                    "token": "+1 (650) 123-4567",
                    "normalizedValue": "(+1) 6501234567",
                    "span": {"end": 17},
                },
            ],
        }
        user_utterance = "+1 (650) 123-4567"
        expected_types = [PhoneNumberEntity]
        expected_values = ["(+1) 6501234567"]
        expected_user_utt_values = ["+1 (650) 123-4567"]
        expected_display_values = ["(+1) 6501234567"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_product(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "PRODUCT",
                    "probability": 0.97431480884552,
                    "token": "iPhone",
                    "span": {"end": 6},
                }
            ],
        }
        user_utterance = "iPhone"
        expected_types = [ProductEntity]
        expected_values = ["iPhone"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_quantity(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "QUANTITY",
                    "probability": 0.8680425882339478,
                    "token": "5 feet",
                    "span": {"end": 6},
                }
            ],
        }
        user_utterance = "5 feet"
        expected_types = [QuantityEntity]
        expected_values = ["5 feet"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_time(self):
        """We only expect one date entity because the NamedEntityExtractor combines the
        two NER outputs into a single entity.
        """
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/time",
                    "token": "1 p.m.",
                    "normalizedValue": "2021-01-15T13:00:00.000Z",
                },
                {
                    "label": "TIME",
                    "probability": 0.9826260805130005,
                    "token": "1 p.m.",
                    "span": {"end": 6},
                },
            ],
        }
        user_utterance = "1 p.m."
        expected_types = [TimeEntity]
        expected_values = [time(hour=13)]
        expected_user_utt_values = ["1 p.m."]
        expected_display_values = ["13:00:00"]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_time_without_duckling(self):
        """Tests that the TimeEntity methods still work properly if there is no
        DUCKLING/time label in the NER output."""
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "TIME",
                    "probability": 0.9826260805130005,
                    "token": "1 p.m.",
                    "span": {"end": 6},
                },
            ],
        }
        user_utterance = "1 p.m."
        expected_types = [TimeEntity]
        expected_values = ["1 p.m."]
        expected_user_utt_values = ["1 p.m."]
        expected_display_values = ["1 p.m."]
        self.check_ner_info(
            ner_info,
            user_utterance,
            expected_types,
            expected_values,
            expected_user_utt_values,
            expected_display_values,
        )

    def test_url(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "DUCKLING/url",
                    "token": "npr.org",
                    "normalizedValue": "npr.org",
                    "span": {"end": 7},
                },
                {
                    "label": "ORG",
                    "probability": 0.9888756275177002,
                    "token": "npr.org",
                    "span": {"end": 7},
                },
            ],
        }
        user_utterance = "npr.org"
        expected_types = [URLEntity, OrganizationEntity]
        expected_values = ["npr.org", "npr.org"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_work_of_art(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "WORK_OF_ART",
                    "probability": 0.99196035,
                    "token": "I Loves You, Porgy",
                    "span": {"end": 18},
                }
            ],
        }
        user_utterance = "I Loves You, Porgy"
        expected_types = [WorkOfArtEntity]
        expected_values = ["I Loves You, Porgy"]
        self.check_ner_info(ner_info, user_utterance, expected_types, expected_values)

    def test_zipcode(self):
        utt = "my zipcode is 94301"
        res = self.named_entity_extractor4.extract(utt)
        self.assertEqual(len(res), 2)
        self.assertTrue(isinstance(res[0], ZipCodeEntity))
        self.assertTrue(isinstance(res[1], LocationEntity))
        self.assertEqual(res[0].value, "94301")
        self.assertEqual(res[1].value, (("ZipCode", "94301"),))


class TestMultiMethods(unittest.TestCase):
    """
    Here, we test extracting the same entity with different methods.
    If there's only one entity in user utt, the different methods
    should extract the same entity value.
    """

    def setUp(self):
        ner_info = {
            "success": True,
            "probabilities": [
                {
                    "label": "PERSON",
                    "probability": 0.9349234,
                    "token": "Tom",
                    "span": {"end": 3},
                }
            ],
        }

        self.spelling_extractor = SpellingEntityExtractor(PersonEntity)
        self.named_entity_extractor = NamedEntityExtractor(ner_info)

    def test_ner_spelling(self):
        utt = "Tom"
        spelling_res = self.spelling_extractor.extract(utt)
        ner_res = self.named_entity_extractor.extract(utt)

        self.assertEqual(spelling_res[0].value, ner_res[0].value)


if __name__ == "__main__":
    unittest.main()
