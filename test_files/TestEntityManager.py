# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest

from Converse.entity.entity_manager import EntityManager, EntityConfig
from Converse.dialog_state_manager.dial_state_manager import DialogState
from Converse.entity.entity import CardinalEntity


class TestEntityConfig(unittest.TestCase):
    def test_entity_config_with_invalid_type(self):
        """
        Test whether the entity manager throws an exception when reading an entity
        config that defines an unknown type
        """
        config = {
            "awesomeEntity": {
                "type": [
                    "CARDINAL",
                    "UNKNOWN_TYPE",  # this will raise an exception
                ],
            }
        }
        with self.assertRaises(ValueError):
            EntityConfig(config)

    def test_entity_config_with_invalid_method(self):
        """
        Test whether the entity manager throws an exception when reading an entity
        config that defines an unknown method
        """
        config = {
            "awesomeEntity": {
                "methods": {
                    "ner": None,
                    "unknown_method": None,  # this will raise an exception
                },
            }
        }
        with self.assertRaises(KeyError):
            EntityConfig(config)

    def test_entity_config_with_invalid_attribute(self):
        """
        Test whether the entity manager throws an exception when reading an entity
        config that defines an unknown attribute
        """
        config = {
            "awesomeEntity": {
                "methods": {
                    "ner": None,
                },
                "type": [
                    "CARDINAL",
                    "STRING",
                ],
                "unknown_attribute": None,  # this will raise an exception
            }
        }
        with self.assertRaises(ValueError):
            EntityConfig(config)


class TestEntityManager(unittest.TestCase):
    def setUp(self):
        self.entity_manager = EntityManager(
            entity_path="test_files/test_entity_config.yaml",
            entity_extraction_path="./Converse/bot_configs/entity_extraction_config.yaml",
        )
        self.cur_states = DialogState.from_dictionary(
            {
                "cur_task": "check_weather",
                "cur_entity_name": "zip_code",
                "cur_entity_types": ["CARDINAL"],
                "confirm_continue": False,
                "need_confirm_entity": False,
                "task_stack": ["check_weather"],
                "exceed_max_turn": False,
                "prev_task": None,
                "entity_methods": {
                    "regex": {"pattern": "\\d{5}"},
                    "spelling": None,
                    "ner": {"required_type": ["CARDINAL"]},
                },
                "spell_entity": None,
                "new_task": None,
                "confirm_entity": False,
                "un_confirmed_entity_value": None,
                "last_verified_entity": None,
                "last_wrong_entity": None,
                "agent_action_type": "API",
                "inform_info": None,
                "api_info": None,
                "updated_info": None,
                "query_info": None,
                "task_with_info": None,
                "confirm_intent": False,
                "un_confirmed_intent": None,
                "multiple_entities": False,
                "repeat_task": False,
            }
        )
        self.info_results = {
            "ner": {
                "success": True,
                "probabilities": [
                    {"label": "ProdMatch/Prod", "token": "9"},
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
                ["my", "zip_code", "is", "9", "4", "3", "2", "9"],
                [(-1, -1, -1)],
            ),
            "coref": {},
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }

        self.methods = self.entity_manager.get_extraction_methods(
            self.cur_states.cur_entity_name
        )
        self.entity_classes = self.entity_manager.get_entity_classes(
            self.cur_states.cur_entity_name
        )
        self.entity_type = self.entity_manager.get_entity_types(
            self.cur_states.cur_entity_name
        )
        self.entity_type_except = self.entity_manager.get_entity_types("personal_email")

    def test_methods(self):
        self.assertEqual(
            self.methods, {"regex": "\\d{5}", "spelling": None, "ner": None}
        )

    def test_entity_class(self):
        self.assertEqual(self.entity_classes, [CardinalEntity])

    def test_entity_type(self):
        """
        get_entity_types function is expected to fetch
        the entity types by entity name from entity config.
        """
        self.assertEqual(self.entity_type, ["CARDINAL"])

    def test_entity_type_except(self):
        """
        get_entity_types is expected to return an empty list because
        personal_email is not in entity config.
        """
        self.assertEqual(self.entity_type_except, [])

    def test_extract(self):
        resp1 = [94329, 943, 9]

        utt = "my zip_code is 9 4 3 2 9"

        res = self.entity_manager.extract_entities(
            utterance=utt,
            methods=self.methods,
            ner_model_output=self.info_results["ner"],
            entity_types=self.entity_classes,
        )
        for entity, target in zip(res, resp1):
            self.assertEqual(entity.value, target)

    def test_type2class(self):
        for entity_type, entity_class in self.entity_manager.type2class.items():
            self.assertEqual(
                self.entity_manager.get_entity_classes(entity_type.lower()),
                [entity_class],
            )

    def test_get_default_extraction_methods(self):
        """Checks that all entity types except PICKLIST entities have a default
        extraction method set in ./entity_extraction_config.yaml. There is no default
        entity extraction method for PICKLIST entities because these entities are
        extracted using fuzzy matching. To use fuzzy matching, the user needs to add
        a list of candidates to match the user utterance in the entity
        configuration file. Since the PICKLIST entity can be used for different kinds
        of entities, it doesn't make sense to set a default list of candidates.
        """
        for entity_type in self.entity_manager.type2class:
            if entity_type not in {"PICKLIST", "STRING"}:
                entity_name = entity_type.lower()
                methods = self.entity_manager.get_extraction_methods(entity_name)
                self.assertGreaterEqual(len(methods), 1)
                self.assertTrue(isinstance(methods, dict))
                if entity_type == "USER_UTT":
                    self.assertEqual(list(methods.keys()), ["user_utterance"])
                elif entity_type in ["EMAIL", "ZIPCODE"]:
                    self.assertEqual(list(methods.keys()), ["ner", "spelling"])
                else:
                    self.assertEqual(list(methods.keys()), ["ner"])


if __name__ == "__main__":
    unittest.main()
