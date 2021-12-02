# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from collections import defaultdict
import datetime
import unittest
from unittest.mock import patch
import uuid

from Converse.dialog_context.dialog_context_manager import DialogContextManager
from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.utils.utils import resp


class TestOrchestrator(unittest.TestCase):
    """
    Orchestrator is the main entry of dialogue management. It organizes
    different modules in the dialogue system.
    We use the test cases to test the behavior of the dialogue system.
    """

    def test_greeting(self):
        greeting = (
            "Hi there, I am the digital assistant for Northern"
            " Trail Information Center. What can I do for you?"
        )
        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        res = dm.reset()
        dmgr.save(cid, ctx)
        self.assertEqual(res, greeting)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_suggest_tasks(self, mocked_info):
        info = {
            "ner": {"success": True},
            "intent": {
                "success": True,
                "intent": "positive",
                "prob": 0.9713575839996338,
                "sent": "Yes",
            },
            "intent_seg": [
                {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "sent": "Yes",
                }
            ],
            "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
            "coref": {"words": ["yes"], "predicted_clusters": [], "top_spans": []},
            "final_intent": {
                "intent": "positive",
                "prob": 0.9713575839996338,
                "uncertain": False,
            },
        }

        mocked_info.return_value = info
        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        dm.reset()
        dmgr.save(cid, ctx)

        suggested_tasks = [
            "I am sorry that I couldn't understand what you said. "
            "Here's what I can do: \n",
            " check local weather\n",
            " convert inch to centimeter\n",
            " check tv plan price\n",
            "You can ask me to do these tasks.",
        ]
        res = dm.process("yes", "yes", ctx)
        dmgr.save(cid, ctx)
        for target in suggested_tasks:
            self.assertIn(target, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_uncertain_intent(self, mocked_info):
        dm = Orchestrator(
            task_path="./test_files/test_tasks.yaml",
            entity_path="./test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        info1 = {
            "ner": {"success": True},
            "final_intent": {
                "intent": "check_weather",
                "prob": 0.6,
                "uncertain": True,
            },
        }
        info2 = {
            "ner": {"success": True},
            "final_intent": {
                "intent": "negative",
                "prob": 0.98,
                "uncertain": False,
            },
        }
        info3 = {
            "ner": {"success": True},
            "final_intent": {
                "intent": "negative",
                "prob": 0.98,
                "uncertain": False,
            },
        }

        resp1 = "So you want to check local weather, right?"
        resp2 = "Is there anything else I can help you with today?"
        resp3 = (
            "Sounds good. I'm glad I could help. Thanks for calling, "
            "and have a good one."
        )

        mocked_info.side_effect = [info1, info2, info3]
        res = dm.process("buy a bike", "buy a bike", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp1, res)
        res = dm.process("no", "no", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp2, res)
        res = dm.process("no", "no", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp3, res, ctx)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_inf(self, mocked_info, mocked_func):
        info1 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "PERSON",
                        "probability": 0.1738394,
                        "token": "inch",
                        "span": {"start": 8, "end": 12},
                    },
                    {
                        "label": "AP/LOCATION",
                        "probability": 0.36957684,
                        "token": "convert inch",
                        "normalizedValue": "LandmarkName:convert inch",
                        "span": {"end": 12},
                    },
                ],
            },
            "intent": {
                "success": True,
                "intent": "convert_inch_to_cm",
                "prob": 0.9614447951316833,
                "sent": "convert inch",
            },
            "intent_seg": [
                {
                    "success": True,
                    "intent": "convert_inch_to_cm",
                    "prob": 0.9614447951316833,
                    "sent": "convert inch",
                }
            ],
            "negation": {"wordlist": ["convert", "inch"], "triplets": [(-1, -1, -1)]},
            "coref": {
                "words": ["convert", "inch"],
                "predicted_clusters": [],
                "top_spans": [],
            },
            "final_intent": {
                "intent": "convert_inch_to_cm",
                "prob": 0.9614447951316833,
                "uncertain": False,
            },
        }
        info2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.91700023,
                        "token": "15",
                        "span": {"end": 2},
                    }
                ],
            },
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "negation": {"wordlist": ["15"], "triplets": [(-1, -1, -1)]},
            "coref": {
                "words": [
                    "Oh",
                    "sure",
                    ",",
                    "I",
                    "'d",
                    "be",
                    "happy",
                    "to",
                    "help",
                    "you",
                    "convert",
                    "inch",
                    "to",
                    "centimeter",
                    ".",
                    "What",
                    "is",
                    "your",
                    "inch",
                    "?",
                    "15",
                ],
                "predicted_clusters": [[(9, 10), (17, 18)]],
                "top_spans": [
                    (3, 4),
                    (8, 9),
                    (9, 10),
                    (10, 11),
                    (11, 14),
                    (17, 18),
                    (17, 19),
                    (20, 21),
                ],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        mocked_info.side_effect = [info1, info2]
        mocked_func.return_value = resp(True, "15.0 inch equals to 38.1 centimeter")

        resp1 = "Oh sure, I'd be happy to help you convert inch to centimeter."
        resp2 = "15.0 inch equals to 38.1 centimeter."

        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        res = dm.process("convert inch", "convert inch", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp1, res)
        res = dm.process("15", "15", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp2, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_repetition(self, mocked_info, mocked_func):
        info1 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "PERSON",
                        "probability": 0.1738394,
                        "token": "inch",
                        "span": {"start": 8, "end": 12},
                    },
                    {
                        "label": "AP/LOCATION",
                        "probability": 0.36957684,
                        "token": "convert inch",
                        "normalizedValue": "LandmarkName:convert inch",
                        "span": {"end": 12},
                    },
                ],
            },
            "final_intent": {
                "intent": "convert_inch_to_cm",
                "prob": 0.9614447951316833,
                "uncertain": False,
            },
        }
        info2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.91700023,
                        "token": "15",
                        "span": {"end": 2},
                    }
                ],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        info3 = {
            "ner": {"success": True},
            "final_intent": {
                "intent": "positive",
                "prob": 0.9713575839996338,
                "uncertain": False,
            },
        }
        info4 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.8483911,
                        "token": "12",
                        "span": {"end": 2},
                    }
                ],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        info5 = {
            "ner": {"success": True},
            "final_intent": {
                "intent": "negative",
                "prob": 0.973708987236023,
                "uncertain": False,
            },
        }
        mocked_info.side_effect = [info1, info2, info3, info4, info5]
        mocked_func.side_effect = [
            resp(True, "15.0 inch equals to 38.1 centimeter"),
            resp(True, "12.0 inch equals to 30.48 centimeter"),
        ]

        resp1 = "Oh sure, I'd be happy to help you convert inch to centimeter."
        resp2 = (
            "15.0 inch equals to 38.1 centimeter. Your request has been completed. "
            "Would you like to convert inch to centimeter again?"
        )
        resp3 = "Oh sure, I'd be happy to help you convert inch to centimeter."
        resp4 = (
            "12.0 inch equals to 30.48 centimeter. Your request has been completed. "
            "Would you like to convert inch to centimeter again?"
        )
        resp5 = "Is there anything else I can help you with today?"

        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        res = dm.process("convert inch", "convert inch", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp1, res)
        res = dm.process("15", "15", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp2, res)
        res = dm.process("yes", "yes", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp3, res)
        res = dm.process("12", "12", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp4, res)
        res = dm.process("no", "no", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp5, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_multiple_entities(self, mocked_info, mocked_func):
        info1 = {
            "ner": {"success": True},
            "negation": (["check", "weather"], [(-1, -1, -1)]),
            "coref": {},
            "final_intent": {
                "intent": "check_weather",
                "prob": 0.9516851902008057,
                "uncertain": False,
            },
        }
        info2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "CARDINAL",
                        "probability": 0.85501295,
                        "token": "94022",
                        "span": {"start": 15, "end": 20},
                    },
                    {
                        "label": "CARDINAL",
                        "probability": 0.30966938,
                        "token": "94301",
                        "span": {"start": 27, "end": 32},
                    },
                    {
                        "label": "AP/LOCATION",
                        "probability": 0.22095564,
                        "token": "94022 oh no 94301",
                        "normalizedValue": (
                            "AddressNumber:94022|StreetNamePostDirectional:oh"
                            "|OccupancyIdentifier:no|ZipCode:94301"
                        ),
                        "span": {"start": 15, "end": 32},
                    },
                ],
            },
            "negation": {
                "wordlist": ["my", "zip", "code", "is", "94022", "oh", "no", "94301"],
                "triplets": [(6, 8, 8)],
            },
            "coref": {},
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        info3 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "ORDINAL",
                        "probability": 0.9386466,
                        "token": "first",
                        "span": {"start": 4, "end": 9},
                    }
                ],
            },
            "negation": {
                "wordlist": ["the", "first", "one"],
                "triplets": [(-1, -1, -1)],
            },
            "coref": {},
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        mocked_info.side_effect = [info1, info2, info3]

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format(
                "broken clouds", "Los Altos", 94022
            ),
        )
        resp1 = "Oh sure, I'd be happy to help you check local weather."
        resp2 = (
            "I got multiple possible answers for zip_code, 94022 and 94301,"
            " which one did you mean?"
        )
        resp3 = [
            "Weather condition is broken clouds at Los Altos, 94022. "
            "Your request has been completed. "
            "Is there anything else I can help you with today?"
        ]
        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        res = dm.process("check_weather", "check_weather", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp1, res)
        res = dm.process(
            "my zip code is 94022 oh no 94301", "my zip code is 94022 oh no 94301", ctx
        )
        dmgr.save(cid, ctx)
        self.assertIn(resp2, res)
        res = dm.process("the first one", "the first one", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(res, resp3)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_simple_task_with_entity(self, mocked_info, mocked_func):
        """
        A user asks for a task and provides its entity within a single turn
        The requested task is a simple task (does not have a subtask tree)
        """
        info1 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "AP/LOCATION",
                        "probability": 0.99873096,
                        "token": "94301",
                        "normalizedValue": "ZipCode:94301",
                        "span": {"start": 18, "end": 23},
                    }
                ],
            },
            "intent": {
                "success": True,
                "intent": "check_weather",
                "prob": 0.9731135964393616,
                "sent": "query the climate",
            },
            "intent_seg": [
                {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9731135964393616,
                    "sent": "query the climate",
                }
            ],
            "negation": {
                "wordlist": ["check_weather", "for", "94301"],
                "triplets": [(-1, -1, -1)],
            },
            "coref": {
                "words": ["check_weather", "for", "94301"],
                "predicted_clusters": [],
                "top_spans": [(2, 3)],
            },
            "final_intent": {
                "intent": "check_weather",
                "prob": 0.9731135964393616,
                "uncertain": False,
            },
        }

        mocked_info.side_effect = [info1, info1]

        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is {} at {}, {}".format(
                    "smoked", "Palo Alto", 94301
                ),
            ),
            TimeoutError(),
        ]

        resp1 = (
            "Oh sure, I'd be happy to help you check local weather. "
            "Weather condition is smoked at Palo Alto, 94301. "
            "Your request has been completed. "
            "Is there anything else I can help you with today?"
        )

        resp2 = (
            "Oh sure, I'd be happy to help you check local weather. "
            "Service time out. "
            "Sorry, I cannot help to finish check local weather. "
            "Is there anything else I can help you with today?"
        )

        dm = Orchestrator(
            task_path="test_files/test_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        res = dm.process("check_weather for 94301", "check_weather for 94301", ctx)
        dmgr.save(cid, ctx)
        self.assertIn(resp1, res)
        # mocked_func.side_effect = TimeoutError()
        res = dm.process("check_weather for 94301", "check_weather for 94301", ctx)
        self.assertIn(resp2, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_from_history_AND1(self, mocked_info, mocked_func):
        """
        We want to test whether we can successfully retrieve from
        the entity history using the AND verification
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_AND1.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/email",
                            "token": "peter@hotmail.com",
                            "normalizedValue": "peter@hotmail.com",
                            "span": {"end": 17},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9078877568244934,
                    "sent": "order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9078877568244934,
                        "sent": "order status",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "check",
                        "order",
                        "status",
                        "for",
                        "peter",
                        "@",
                        "hotmail.com",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "check",
                        "order",
                        "status",
                        "for",
                        "peter",
                        "@",
                        "hotmail.com",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3), (4, 7)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9078877568244934,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8238977,
                            "token": "94301",
                            "span": {"start": 20, "end": 25},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9361704,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"start": 20, "end": 25},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8554752469062805,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8554752469062805,
                        "sent": "correct",
                    }
                ],
                "negation": {
                    "wordlist": ["yes", "and", "zip", "code", "is", "94301"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "agent",
                        "response",
                        "yes",
                        "and",
                        "zip",
                        "code",
                        "is",
                        "94301",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2), (4, 6), (7, 8)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8554752469062805,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            resp(True, "Verified"),
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status for peter@hotmail.com",
            "yes and zip code is 94301",
        ]

        target_responses = [
            (
                "Oh sure, I'd be happy to help you check your order status. "
                "First, I need to pull up your account. "
                "Okay, so P E T E R at hotmail dot com?"
            ),
            (
                "I have verified your identity. "
                "Please provide your order id for your order status."
            ),
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            self.assertIn(target, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_from_history_AND2(self, mocked_info, mocked_func):
        """
        We want to test whether we can successfully retrieve from the
        entity history using the AND verification
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_AND2.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/email",
                            "token": "peter@hotmail.com",
                            "normalizedValue": "peter@hotmail.com",
                            "span": {"end": 17},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9078877568244934,
                    "sent": "order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9078877568244934,
                        "sent": "order status",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "check",
                        "order",
                        "status",
                        "for",
                        "peter",
                        "@",
                        "hotmail.com",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "check",
                        "order",
                        "status",
                        "for",
                        "peter",
                        "@",
                        "hotmail.com",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3), (4, 7)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9078877568244934,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8238977,
                            "token": "94301",
                            "span": {"start": 20, "end": 25},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9361704,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"start": 20, "end": 25},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8554752469062805,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8554752469062805,
                        "sent": "correct",
                    }
                ],
                "negation": {
                    "wordlist": ["yes", "and", "zip", "code", "is", "94301"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "agent",
                        "response",
                        "yes",
                        "and",
                        "zip",
                        "code",
                        "is",
                        "94301",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2), (4, 6), (7, 8)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8554752469062805,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Okay",
                        ",",
                        "so",
                        "peter",
                        "@",
                        "hotmail.com",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23)],
                        [(3, 4), (17, 18)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (6, 7),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (18, 19),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (28, 31),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            resp(True, "Verified"),
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status for peter@hotmail.com",
            "94301",
            "yes",
        ]

        target_responses = [
            [
                (
                    "Oh sure, I'd be happy to help you"
                    " check your order status. "
                    "First, I need to pull up your account."
                ),
                "your zip code?",
            ],
            ["Okay, so P E T E R at hotmail dot com?"],
            [
                (
                    "One moment please. Your order status is 10 pizza,"
                    " placed but not yet shipped. "
                    "Please provide your order id for your order details."
                )
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_from_history_OR(self, mocked_info, mocked_func):
        """
        We want to test whether we can successfully retrieve from
        the entity history using the OR verification
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_OR.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.5564686,
                            "token": "94301",
                            "span": {"start": 23, "end": 28},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9754588,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"start": 23, "end": 28},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.8545706868171692,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.8545706868171692,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status", "for", "94301"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "agent",
                        "response",
                        "check",
                        "order",
                        "status",
                        "for",
                        "94301",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2), (6, 7)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.8545706868171692,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": ["agent", "response", "no"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2)],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status for 94301",
            "no",
        ]

        # since the target response consists of multiple sentences,
        # where each sentence can take in multiple variations,
        # we simply test that each of the main component is present
        # in the response
        # dim0: response for each turn
        # dim1: target sentences that should be present in all variations
        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            [
                ("I am sorry," " but I could not recognize your email_address. "),
                (
                    "I have verified your identity. "
                    "Please provide your order id for your order status."
                ),
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_from_history_two_entities_are_numbers(
        self, mocked_info, mocked_func
    ):
        """
        We want to test whether entities are reused if both entities have the
        same entity type but have different entity names. We expect this to be
        true for the current implementation.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_OR.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "update_order",
                    "prob": 0.8217718601226807,
                    "sent": "Can you add more to my order",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "update_order",
                        "prob": 0.8217718601226807,
                        "sent": "Can you add more to my order",
                    }
                ],
                "negation": {
                    "wordlist": ["add", "more", "to", "my", "order"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "add",
                        "more",
                        "to",
                        "my",
                        "order",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)], [(19, 20), (24, 25)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (5, 13),
                        (9, 13),
                        (16, 17),
                        (17, 18),
                        (19, 20),
                        (21, 22),
                        (24, 25),
                        (24, 26),
                    ],
                },
                "final_intent": {
                    "intent": "update_order",
                    "prob": 0.8217718601226807,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.6297982335090637,
                    "sent": "Sorry",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.6297982335090637,
                        "sent": "Sorry",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "do", "n't", "have", "an", "email", "address"],
                    "triplets": [(2, 3, 7)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "email",
                        "address",
                        "?",
                        "I",
                        "do",
                        "n't",
                        "have",
                        "an",
                        "email",
                        "address",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (13, 14), (23, 24), (29, 30), (33, 34)],
                        [(3, 4), (18, 19), (27, 28)],
                        [(29, 32), (37, 40)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (13, 14),
                        (13, 15),
                        (18, 19),
                        (21, 22),
                        (23, 24),
                        (23, 25),
                        (27, 28),
                        (28, 29),
                        (29, 30),
                        (29, 32),
                        (33, 34),
                        (37, 40),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.6297982335090637,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8565762639045715,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365082263946533,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "I",
                        "am",
                        "sorry",
                        ",",
                        "but",
                        "I",
                        "could",
                        "not",
                        "recognize",
                        "your",
                        "email_address",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (5, 6), (13, 14)],
                        [(9, 10), (15, 16)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (5, 6),
                        (9, 10),
                        (9, 11),
                        (13, 14),
                        (15, 16),
                        (15, 18),
                        (19, 20),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.9436145424842834,
                            "token": "10",
                            "span": {"end": 2},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["10"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "How",
                        "many",
                        "do",
                        "you",
                        "want",
                        "to",
                        "add",
                        "?",
                        "10",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (4, 5), (6, 7), (11, 12)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ",", "so", "10", "?", "yes"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (3, 4)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            resp(True, "10 pizza, placed but not yet shipped"),
            resp(True, "20"),
        ]

        user_inputs = [
            "add more to my order",
            "I don't have an email address",
            "94301",
            "10",
            "yes",
        ]

        # since the target response consists of multiple sentences,
        # where each sentence can take in multiple variations,
        # we simply test that each of the main component is present
        # in the response
        # dim0: response for each turn
        # dim1: target sentences that should be present in all variations
        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you add more to your order. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            [
                ("I am sorry," " but I could not recognize your email_address. "),
                "your zip code?",
            ],
            ["How many do you want to add?"],
            ["Okay, so 10?"],
            ["Now you have ordered 20 pieces."],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_other_named_entities(self, mocked_info):
        """
        We want to test whether we can successfully get task done
        without writing subclass from StringEntity
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_other_ner.yaml",
            entity_path="./test_files/test_entity_other_ner.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PLACEHOLDER_LABEL",
                            "probability": 0.9448586106300354,
                            "token": "next Friday.",
                            "span": {"start": 32, "end": 44},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "schedule_meeting",
                    "prob": 0.9854496717453003,
                    "sent": "I want to set up a meeting",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "schedule_meeting",
                        "prob": 0.9854496717453003,
                        "sent": "I want to set up a meeting",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "i",
                        "want",
                        "to",
                        "schedule",
                        "a",
                        "meeting",
                        "on",
                        "next",
                        "friday",
                        ".",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "I",
                        "want",
                        "to",
                        "schedule",
                        "a",
                        "meeting",
                        "on",
                        "next",
                        "Friday",
                        ".",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)], [(19, 20), (21, 22)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (9, 13),
                        (16, 17),
                        (17, 18),
                        (19, 20),
                        (21, 22),
                        (22, 23),
                        (24, 25),
                        (25, 27),
                        (25, 30),
                        (28, 30),
                    ],
                },
                "final_intent": {
                    "intent": "schedule_meeting",
                    "prob": 0.9854496717453003,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "schedule",
                        "a",
                        "meeting",
                        ".",
                        "Got",
                        "it",
                        ".",
                        "Your",
                        "meeting",
                        "is",
                        "scheduled",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [
                        [(11, 13), (15, 16)],
                        [(9, 10), (17, 18), (29, 30)],
                        [(3, 4), (26, 27)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (15, 16),
                        (17, 18),
                        (17, 19),
                        (20, 21),
                        (24, 32),
                        (26, 27),
                        (29, 30),
                        (31, 32),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
        ]
        user_inputs = ["I want to schedule a meeting on next Friday.", "no"]

        target_responses = [
            [
                (
                    "Oh sure, I'd be happy to help you schedule a meeting. "
                    "Got it. "
                    "Your meeting is scheduled. "
                    "Is there anything else I can help you with today?"
                )
            ],
            [
                (
                    "Sounds good. I'm glad I could help. "
                    "Thanks for calling, and have a good one."
                )
            ],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_forget_entity(self, mocked_info, mocked_func, mocked_api):
        """
        Use zip code as an entity for user verification, but it is configured
        to be erased from the history. A subsequent task is to check weather that also
        requires the zip code. We want to test that the zip code is not retrieved from
        the history
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_forget_entity.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "San Mateo", 94403),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351425647735596,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.8558374643325806,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29)],
                        [(3, 4), (17, 18), (26, 27)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (28, 29),
                        (28, 31),
                        (32, 33),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "I",
                        "have",
                        "verified",
                        "your",
                        "identity",
                        ".",
                        "Please",
                        "provide",
                        "your",
                        "order",
                        "id",
                        "for",
                        "your",
                        "order",
                        "status",
                        ".",
                        "check",
                        "weather",
                    ],
                    "predicted_clusters": [[(6, 7), (11, 12), (15, 16)]],
                    "top_spans": [
                        (1, 2),
                        (3, 4),
                        (5, 6),
                        (6, 7),
                        (6, 8),
                        (11, 12),
                        (15, 16),
                        (15, 18),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.29375746846199036,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9637288451194763,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Now",
                        "let",
                        "me",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94403",
                    ],
                    "predicted_clusters": [[(4, 5), (11, 12)]],
                    "top_spans": [(2, 3), (4, 5), (5, 6), (6, 8), (11, 12), (15, 16)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
        ]

        user_inputs = [
            "check order status",
            "94301",
            "check weather",
            "94403",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your zip code?",
            ],
            [
                "I have verified your identity. ",
                "Please provide your order id for your order status.",
            ],
            ["Now let me help you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at San Mateo, 94403. "
                    "Your request has been completed."
                ),
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_not_forget_entity_by_default(self, mocked_info, mocked_func):
        """
        We want to test that not specifying the forget field, we keep the entity
        in history as before. The zip_code entity from the check_weather task is used
        in the verify_user subtask in the check order status task.
        Note that check_weather task's zip_code entity is not specified with 'forget'
        key in the task yaml file
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_forget_entity.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9847128391265869,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.85657626,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365082,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["94301"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9282979369163513,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "check weather",
            "94301",
            "check order status",
        ]

        target_responses = [
            ["I'd be happy to help you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at Palo Alto, 94301. "
                    "Your request has been completed."
                ),
            ],
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
            ],
            [
                "Your order status is 10 pizza, placed but not yet shipped. "
                "Please provide your order id for your order details."
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_do_not_retrieve_entity(self, mocked_info, mocked_func, mocked_api):
        """
        Use zip code as an entity for both user verification and check weather tasks.
        However, the weather task's zip code is configured not to retrieve the entity
        from history.
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_entity_selective_retrieval.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "San Mateo", 94403),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9282979369163513,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.85657626,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365082,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["94301"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9847128391265869,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7607909,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.80640703,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["94403"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status",
            "94301",
            "check weather",
            "94403",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your zip code?",
            ],
            [
                "Your order status is 10 pizza, placed but not yet shipped. "
                "Please provide your order id for your order details."
            ],
            ["Now let me help you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at San Mateo, 94403. "
                    "Your request has been completed."
                ),
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_confirm_override_for_retrieved_entity(
        self, mocked_info, mocked_func, mocked_api
    ):
        """
        Test whether the task config's `confirm` set to true will override
        `confirm_retrieved` value (in this case, not set --> default no)
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_confirm.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351426,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.85583746,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [[(3, 4), (15, 16)], [(9, 10), (17, 18)]],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (15, 16),
                        (17, 18),
                        (17, 20),
                        (21, 22),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "clear",
                        "sky",
                        "at",
                        "Palo",
                        "Alto",
                        ",",
                        "94301",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "order",
                        "status",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (23, 24),
                        (24, 25),
                        (26, 27),
                        (28, 31),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "sent": "Yes",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9713575839996338,
                        "sent": "Yes",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Your",
                        "zip",
                        "code",
                        "is",
                        "94301",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (25, 26)],
                        [(3, 4), (17, 18)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (22, 28),
                        (25, 26),
                        (25, 28),
                        (32, 33),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "uncertain": False,
                },
            },
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check weather",
            "94301",
            "check order status",
            "yes",
        ]

        target_responses = [
            ["you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at Palo Alto, 94301. "
                    "Your request has been completed."
                ),
            ],
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account. "
                    "Your zip code is 94301. Is that correct?"
                ),
            ],
            [
                "I have verified your identity. ",
                "Please provide your order id for your order status.",
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_confirm_retrieved_default(self, mocked_info, mocked_func, mocked_api):
        """
        If "confirm_retrieved" key is not provided, it is assumed to be true
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_confirm_default.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351426,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.85583746,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [[(9, 10), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (16, 17),
                        (16, 19),
                        (20, 21),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "clear",
                        "sky",
                        "at",
                        "Palo",
                        "Alto",
                        ",",
                        "94301",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "order",
                        "status",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (23, 24),
                        (24, 25),
                        (26, 27),
                        (28, 31),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "sent": "Yes",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9713575839996338,
                        "sent": "Yes",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Your",
                        "zip",
                        "code",
                        "is",
                        "94301",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (25, 26)],
                        [(3, 4), (17, 18)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (22, 28),
                        (25, 26),
                        (25, 28),
                        (32, 33),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "uncertain": False,
                },
            },
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check weather",
            "94301",
            "check order status",
            "yes",
        ]

        target_responses = [
            ["you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at Palo Alto, 94301. "
                    "Your request has been completed."
                ),
            ],
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account. "
                    "Your zip code is 94301. Is that correct?"
                ),
            ],
            [
                "Your order status is 10 pizza, placed but not yet shipped. "
                "Please provide your order id for your order details."
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_confirm_retrieved1(self, mocked_info, mocked_func, mocked_api):
        """
        Test whether the task config's `confirm_retrieved` set will invoke
        confirmation on the entity that is retrieved from the past
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_confirm.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351425647735596,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.8558374643325806,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29)],
                        [(3, 4), (17, 18), (26, 27)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (28, 29),
                        (28, 31),
                        (32, 33),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "sent": "Yes",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9713575839996338,
                        "sent": "Yes",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ",", "so", "94301", "?", "yes"],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4), (5, 6)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8254072666168213,
                            "token": "1",
                            "span": {"end": 1},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.4677410423755646,
                            "token": "1",
                            "normalizedValue": "AddressNumber:1",
                            "span": {"end": 1},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7362222671508789,
                    "sent": "Sure",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7362222671508789,
                        "sent": "Sure",
                    }
                ],
                "negation": {"wordlist": ["1"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "I",
                        "have",
                        "verified",
                        "your",
                        "identity",
                        ".",
                        "Please",
                        "provide",
                        "your",
                        "order",
                        "id",
                        "for",
                        "your",
                        "order",
                        "status",
                        ".",
                        "1",
                    ],
                    "predicted_clusters": [[(6, 7), (11, 12), (15, 16)]],
                    "top_spans": [
                        (1, 2),
                        (3, 4),
                        (5, 6),
                        (6, 7),
                        (6, 8),
                        (11, 12),
                        (15, 16),
                        (15, 18),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7362222671508789,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "One",
                        "moment",
                        "please",
                        ".",
                        "Your",
                        "order",
                        "status",
                        "is",
                        "placed",
                        "but",
                        "not",
                        "yet",
                        "shipped",
                        ".",
                        "That",
                        "is",
                        "all",
                        "the",
                        "information",
                        "that",
                        "I",
                        "have",
                        "on",
                        "your",
                        "order",
                        "status",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "check",
                        "the",
                        "status",
                        "of",
                        "another",
                        "order",
                        "?",
                        "check",
                        "weather",
                    ],
                    "predicted_clusters": [
                        [(4, 5), (23, 24), (28, 29)],
                        [(4, 7), (23, 26)],
                    ],
                    "top_spans": [
                        (0, 2),
                        (4, 5),
                        (4, 7),
                        (8, 9),
                        (14, 15),
                        (16, 26),
                        (16, 37),
                        (20, 21),
                        (23, 24),
                        (23, 26),
                        (28, 29),
                        (31, 32),
                        (32, 37),
                        (35, 37),
                        (38, 39),
                        (39, 40),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "sent": "Yes",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9713575839996338,
                        "sent": "Yes",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Your",
                        "zip",
                        "code",
                        "is",
                        "94301",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [[(9, 10), (14, 15)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 17),
                        (14, 15),
                        (14, 17),
                        (18, 19),
                        (21, 22),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "uncertain": False,
                },
            },
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status",
            "94301",
            "yes",
            "1",
            "check weather",
            "yes",
        ]

        target_responses = [
            [
                "help you check your order status. "
                "First, I need to pull up your account. ",
                "your zip code?",
            ],
            ["so 94301?"],
            [
                "I have verified your identity.",
                "Please provide your order id for your order status.",
            ],
            [
                "One moment please. "
                "Your order status is 10 pizza, placed but not yet shipped. "
                "That is all the information that I have on your order status."
            ],
            [
                "help you check local weather",
                "Your zip code is 94301. Is that correct?",
            ],
            ["Weather condition is clear sky at Palo Alto, 94301."],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_confirm_retrieved2(self, mocked_info, mocked_func):
        """
        Test whether the task config's `confirm_retrieved` set will not invoke
        confirmation on the entity that is not retrieved from the past
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_confirm.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351426,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.85583746,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["94301"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = [
            "check weather",
            "94301",
        ]

        target_responses = [
            ["you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at Palo Alto, 94301. "
                    "Your request has been completed."
                ),
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_reject_retrieved_entity_after_confirmation_and_provide_a_new_entity(
        self, mocked_info, mocked_func
    ):
        """
        This test checks if the bot accepts the new entity when the user rejects the
        entity that the bot retrieved from the history. It also checks that the task
        turn count (task_turns in the
        Converse.dialog_state_manager.dial_state_manager.py) is reset to 0 after tasks
        are completed. The task turn limit for the check the weather task
        is 2 and the check the weather task turn count would be 3 during the last
        turn of this test if it is not reset after the bot finishes checking the
        weather for the zip code 94403, therefore it would cause the bot to quit the
        task before it checked the weather for the zip code 94301.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_chain.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is few clouds at San Mateo, 94403",
            ),
            resp(True, "Weather condition is clear sky at Palo Alto, 94301"),
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.29375747,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.96372885,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94403",
                    ],
                    "predicted_clusters": [[(3, 4), (15, 16)], [(9, 10), (17, 18)]],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (15, 16),
                        (17, 18),
                        (17, 20),
                        (21, 22),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "few",
                        "clouds",
                        "at",
                        "San",
                        "Mateo",
                        ",",
                        "94403",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "weather",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (3, 13),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (24, 25),
                        (26, 27),
                        (28, 29),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.973708987236023,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Your",
                        "zip",
                        "code",
                        "is",
                        "94403",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [[(9, 10), (14, 15)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 17),
                        (14, 15),
                        (14, 17),
                        (18, 19),
                        (21, 22),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351426,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.85583746,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["What", "is", "your", "zip", "code", "?", "94301"],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3), (6, 7)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = ["check weather", "94403", "check weather", "no", "94301"]

        target_responses = [
            ["Oh sure, I'd be happy to help you check local weather.", "zip code?"],
            [
                "Weather condition is few clouds at San Mateo, 94403. "
                "Your request has been completed. "
                "Is there anything else I can help you with today?"
            ],
            [
                "Oh sure, I'd be happy to help you check local weather. "
                "Your zip code is 94403. Is that correct?"
            ],
            ["zip code?"],
            [
                "Weather condition is clear sky at Palo Alto, 94301. "
                "Your request has been completed. "
                "Is there anything else I can help you with today?"
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_reject_retrieved_entity_after_confirmation_and_provide_a_new_entity_in_a_single_turn(
        self, mocked_info, mocked_func
    ):
        """
        This test checks if the bot accepts the new entity when the user rejects the
        entity that the bot retrieved from the history and provides a new entity in
        the same turn. We expect the bot to use the new entity instead of the entity
        that was retrieved from history.

        This test also checks that the state "confirm_entity" is reset after the user
        provides a new entity by checking that bot responds with "Sounds good. I'm
        glad I could help. Thanks for calling, and have a good one." which indicates
        that the task succeeded. If "confirm_entity" is not reset to None, the bot
        will respond with "I couldn't help you with your request. Let me forward this
        case to one of our professional agents. Please wait for 5 minutes." in the last
        turn.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_chain.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is few clouds at San Mateo, 94403",
            ),
            resp(True, "Weather condition is clear sky at Palo Alto, 94301"),
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.29375747,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.96372885,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94403",
                    ],
                    "predicted_clusters": [[(3, 4), (15, 16)], [(9, 10), (17, 18)]],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (15, 16),
                        (17, 18),
                        (17, 20),
                        (21, 22),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9516851902008057,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "few",
                        "clouds",
                        "at",
                        "San",
                        "Mateo",
                        ",",
                        "94403",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "weather",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (3, 13),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (24, 25),
                        (26, 27),
                        (28, 29),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9516851902008057,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9990689158439636,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"start": 9, "end": 14},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.6698583960533142,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.6698583960533142,
                        "sent": "No",
                    }
                ],
                "negation": {
                    "wordlist": ["no", ",", "it", "'s", "94301"],
                    "triplets": [(0, 3, 4)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Your",
                        "zip",
                        "code",
                        "is",
                        "94403",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "no",
                        ",",
                        "it",
                        "'s",
                        "94301",
                    ],
                    "predicted_clusters": [[(9, 10), (14, 15)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 17),
                        (14, 15),
                        (14, 17),
                        (18, 19),
                        (21, 22),
                        (26, 27),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.6698583960533142,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.973708987236023,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "clear",
                        "sky",
                        "at",
                        "Palo",
                        "Alto",
                        ",",
                        "94301",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (23, 24),
                        (24, 25),
                        (26, 27),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "check weather",
            "94403",
            "check weather",
            "no, it's 94301",
            "no",
        ]

        target_responses = [
            ["Oh sure, I'd be happy to help you check local weather.", "zip code?"],
            [
                "Weather condition is few clouds at San Mateo, 94403. "
                "Your request has been completed. "
                "Is there anything else I can help you with today?"
            ],
            [
                "Oh sure, I'd be happy to help you check local weather. Your zip code is 94403. Is that correct?"
            ],
            [
                "Weather condition is clear sky at Palo Alto, 94301. "
                "Your request has been completed. "
                "Is there anything else I can help you with today?"
            ],
            [
                "Sounds good. I'm glad I could help. "
                "Thanks for calling, and have a good one."
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_retrieve_entity_single_turn(self, mocked_info, mocked_func):
        """
        Check weather's zip code is configured not to retrieve entity from the history.
        However, it should retrieve the entity from the same turn, as in
        "check weather in 94301"
        The config is in the task's yaml's entities dictionary with the key "retrieve"
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_entity_selective_retrieval.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "San Mateo", 94403),
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.28100428,
                            "token": "94403",
                            "span": {"start": 17, "end": 22},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.99992883,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"start": 17, "end": 22},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9868011474609375,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9868011474609375,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather", "in", "94403"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather", "in", "94403"],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4)],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9868011474609375,
                    "uncertain": False,
                },
            }
        ]

        user_inputs = [
            "check weather in 94403",
        ]

        target_responses = [
            [
                "you check local weather.",
                "Weather condition is clear sky at San Mateo, 94403. "
                "Your request has been completed.",
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_do_not_retrieve_entity_by_default(self, mocked_info, mocked_func):
        """
        Use zip code as an entity for both user verification and check weather tasks.
        The verification task's zip code entity's retrieval config is not set.
        This should by default retrieve from the history.
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_entity_selective_retrieval.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "Palo Alto", 94301),
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9847128391265869,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9847128391265869,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.85657626,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365082,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["94301"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9282979369163513,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "check weather",
            "94301",
            "check order status",
        ]

        target_responses = [
            ["I'd be happy to help you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at Palo Alto, 94301. "
                    "Your request has been completed."
                ),
            ],
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
            ],
            [
                "Your order status is 10 pizza, placed but not yet shipped. "
                "Please provide your order id for your order details."
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_chain(self, mocked_info, mocked_func):
        """
        Test situation where the bot is currently helping the user with task A
            and the user asks to start task B before task A is completed.
        After the bot helps the user complete task B, it should resume task A.
        Here task A and task B are independent, they don't share a subtask C
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_chain.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9282979369163513,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "check",
                        "order",
                        "status",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (5, 13),
                        (9, 13),
                        (16, 17),
                        (17, 18),
                        (19, 20),
                        (21, 24),
                        (22, 24),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "today",
                            "normalizedValue": "2020-10-14T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.9209828972816467,
                            "token": "today's",
                            "span": {"start": 23, "end": 30},
                        },
                        {
                            "label": "ORDINAL",
                            "probability": 0.6959046125411987,
                            "token": "first?",
                            "span": {"start": 46, "end": 52},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9781941771507263,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9781941771507263,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "oh",
                        "wait",
                        ",",
                        "can",
                        "you",
                        "check",
                        "today",
                        "'s",
                        "weather",
                        "for",
                        "me",
                        "first",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "What",
                        "is",
                        "your",
                        "email",
                        "address",
                        "?",
                        "oh",
                        "wait",
                        ",",
                        "can",
                        "you",
                        "check",
                        "today",
                        "'s",
                        "weather",
                        "for",
                        "me",
                        "first",
                        "?",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (27, 28), (41, 42)],
                        [(3, 4), (17, 18), (35, 36)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (27, 28),
                        (27, 30),
                        (35, 36),
                        (36, 37),
                        (37, 39),
                        (37, 40),
                        (41, 42),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9781941771507263,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7607908844947815,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.8064070343971252,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Now",
                        "let",
                        "me",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip_code",
                        "?",
                        "94403",
                    ],
                    "predicted_clusters": [[(4, 5), (11, 12)]],
                    "top_spans": [
                        (2, 3),
                        (4, 5),
                        (6, 8),
                        (11, 12),
                        (11, 13),
                        (14, 15),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "San Mateo", 94403),
        )

        user_inputs = [
            "check order status",
            "oh wait, can you check today's weather for me first?",
            "94403",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            ["Now let me help you check local weather.", "your zip code?"],
            [
                (
                    "Weather condition is clear sky at San Mateo, 94403. "
                    "Your request has been completed."
                ),
                "your email address?",
            ],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_chain_with_shared_task(self, mocked_info, mocked_func):
        """

        Test situation where the bot is currently helping the user with task A
        and the user asks to start task B before task A is completed. Here task A
        and task B share a subtask C. After the bot helps the user complete
        task B (and task C), it should resume task A instead of repeat task C.

        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_chain.yaml",
            entity_path="./test_files/test_task_chain_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.8893790245056152,
                    "sent": "order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.8893790245056152,
                        "sent": "order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "check",
                        "order",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (5, 13),
                        (9, 13),
                        (16, 17),
                        (17, 18),
                        (19, 20),
                        (21, 22),
                        (21, 23),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.8893790245056152,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/email",
                            "token": "peter@hotmail.com",
                            "normalizedValue": "peter@hotmail.com",
                            "span": {"end": 17},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["peter", "@", "hotmail.com"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "email",
                        "address",
                        "?",
                        "peter",
                        "@",
                        "hotmail.com",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29)],
                        [(3, 4), (17, 18), (26, 27)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (27, 28),
                        (28, 29),
                        (28, 31),
                        (32, 35),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Okay",
                        ",",
                        "so",
                        "K",
                        "I",
                        "N",
                        "G",
                        "S",
                        "I",
                        "at",
                        "salesforce",
                        "dot",
                        "com",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (3, 13),
                        (4, 5),
                        (8, 9),
                        (8, 13),
                        (10, 11),
                        (10, 13),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.9327037334442139,
                            "token": "10",
                            "span": {"start": 4, "end": 6},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "update_order",
                    "prob": 0.9076326489448547,
                    "sent": "Can you add more to my order",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "update_order",
                        "prob": 0.9076326489448547,
                        "sent": "Can you add more to my order",
                    }
                ],
                "negation": {
                    "wordlist": ["add", "10", "more", "to", "my", "order"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "One",
                        "moment",
                        "please",
                        ".",
                        "Your",
                        "order",
                        "status",
                        "is",
                        "10",
                        "pizza",
                        ",",
                        "placed",
                        "but",
                        "not",
                        "yet",
                        "shipped",
                        ".",
                        "Please",
                        "provide",
                        "your",
                        "order",
                        "id",
                        "for",
                        "your",
                        "order",
                        "details",
                        ".",
                        "add",
                        "10",
                        "more",
                        "to",
                        "my",
                        "order",
                    ],
                    "predicted_clusters": [[(4, 5), (19, 20), (23, 24), (31, 32)]],
                    "top_spans": [
                        (0, 2),
                        (4, 5),
                        (4, 7),
                        (8, 16),
                        (8, 26),
                        (18, 19),
                        (19, 20),
                        (19, 22),
                        (23, 24),
                        (23, 26),
                        (27, 28),
                        (31, 32),
                        (31, 33),
                    ],
                },
                "final_intent": {
                    "intent": "update_order",
                    "prob": 0.9076326489448547,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Now",
                        "let",
                        "me",
                        "help",
                        "you",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        ".",
                        "Okay",
                        ",",
                        "so",
                        "10",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [[(4, 5), (8, 9)]],
                    "top_spans": [(2, 3), (3, 4), (4, 5), (5, 6), (8, 9), (8, 10)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Now",
                        "you",
                        "have",
                        "ordered",
                        "20",
                        "pieces",
                        ".",
                        "Your",
                        "order",
                        "has",
                        "been",
                        "updated",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "add",
                        "more",
                        "items",
                        "to",
                        "your",
                        "order",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [
                        [(4, 5), (10, 11), (17, 18), (24, 25)],
                        [(10, 12), (24, 26)],
                    ],
                    "top_spans": [
                        (1, 2),
                        (4, 5),
                        (6, 7),
                        (7, 9),
                        (10, 11),
                        (10, 12),
                        (14, 15),
                        (17, 18),
                        (21, 23),
                        (24, 25),
                        (24, 26),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "check order",
            "peter@hotmail.com",
            "yes",
            "add 10 more to my order",
            "yes",
            "no",
        ]

        mocked_func.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped."),
            resp(True, "20"),
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            ["Okay, so P E T E R at hotmail dot com?"],
            [
                "One moment please.",
                "Your order status is 10 pizza, placed but not yet shipped.",
                "Please provide your order id for your order details.",
            ],
            ["Now let me help you add more to your order. Okay, so 10?"],
            [
                "Got it. Now you have ordered 20 pieces.",
                "Your order has been updated.",
                "Would you like to add more items to your order?",
            ],
            ["Please provide your order id for your order details."],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_fail_entity_with_OR_node(self, mocked_info, mocked_func):
        """
        Tests if the bot continues to the next child of the OR node if the user does
        not have the current entity.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_OR.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        user_inputs = [
            "check order status",
            "I don't have an email address",
            "94301",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            [
                "I am sorry, but I could not recognize your email_address.",
                "your zip code?",
            ],
            [
                (
                    "I have verified your identity. "
                    "Please provide your order id for your order status."
                )
            ],
        ]

        mocked_func.side_effect = [
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9282979369163513,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "check",
                        "order",
                        "status",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (5, 13),
                        (9, 13),
                        (16, 17),
                        (17, 18),
                        (19, 20),
                        (21, 24),
                        (22, 24),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9282979369163513,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.6297982335090637,
                    "sent": "Sorry",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.6297982335090637,
                        "sent": "Sorry",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "do", "n't", "have", "an", "email", "address"],
                    "triplets": [(2, 3, 7)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "What",
                        "is",
                        "your",
                        "email",
                        "address",
                        "?",
                        "I",
                        "do",
                        "n't",
                        "have",
                        "an",
                        "email",
                        "address",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (27, 28), (31, 32)],
                        [(3, 4), (17, 18)],
                        [(27, 30), (35, 38)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (27, 28),
                        (27, 30),
                        (31, 32),
                        (34, 35),
                        (35, 38),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.6297982335090637,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8565762639045715,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365082263946533,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "I",
                        "am",
                        "sorry",
                        ",",
                        "but",
                        "I",
                        "could",
                        "not",
                        "recognize",
                        "your",
                        "email_address",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [[(0, 1), (5, 6)], [(9, 10), (14, 15)]],
                    "top_spans": [
                        (0, 1),
                        (5, 6),
                        (9, 10),
                        (9, 11),
                        (14, 15),
                        (14, 17),
                        (18, 19),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_fail_entity_with_AND_node(self, mocked_info):
        """
        Tests if the task fails if the user does not have the current entity in the
        AND node.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_tree_AND1.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        user_inputs = [
            "check order status",
            "email address",
            "I don't have it",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "your email address?",
            ],
            [
                (
                    "I am sorry, but I could not recognize your email_address. "
                    "I couldn't help you with your request. "
                    "Let me forward this case to one of our professional agents. "
                    "Please wait for 5 minutes."
                )
            ],
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["email", "address"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "email",
                        "address",
                        "?",
                        "email",
                        "address",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29)],
                        [(3, 4), (17, 18), (26, 27)],
                        [(28, 31), (32, 34)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (28, 29),
                        (28, 31),
                        (32, 34),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9469292163848877,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9469292163848877,
                        "sent": "No",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "do", "n't", "have", "it"],
                    "triplets": [(2, 3, 4)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "email",
                        "address",
                        "?",
                        "I",
                        "do",
                        "n't",
                        "have",
                        "it",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29), (32, 33)],
                        [(3, 4), (17, 18), (26, 27)],
                        [(28, 31), (36, 37)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (28, 29),
                        (28, 31),
                        (32, 33),
                        (36, 37),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9469292163848877,
                    "uncertain": False,
                },
            },
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_normalization(self, mocked_info):
        """Tests that the normalized entity displayed by calling entity.display_value()
        instead of relying on the string representation of the normalized value. The
        date is formatted using a custom format string of 'month day, year' in the
        .display_value() method of DateEntity. By testing for the date in this format,
        we can check if entity.display_value() is being called.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_entity_normalization.yaml",
            entity_path="./test_files/test_entity_normalization_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "make_reservation",
                    "prob": 0.8780724406242371,
                    "sent": "I want to make a reservation",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "make_reservation",
                        "prob": 0.8780724406242371,
                        "sent": "I want to make a reservation",
                    }
                ],
                "negation": {
                    "wordlist": ["make", "a", "reservation"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["make", "a", "reservation"],
                    "predicted_clusters": [],
                    "top_spans": [(1, 3)],
                },
                "final_intent": {
                    "intent": "make_reservation",
                    "prob": 0.8780724406242371,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "1/25/21",
                            "normalizedValue": "2021-01-25T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8888510465621948,
                            "token": "1/25/21",
                            "span": {"end": 7},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.7301806807518005,
                            "token": "1/25/21",
                            "normalizedValue": "AddressNumber:1/25/21",
                            "span": {"end": 7},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["1/25/21"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "make",
                        "reservation",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "date",
                        "?",
                        "1/25/21",
                    ],
                    "predicted_clusters": [[(3, 4), (14, 15)], [(9, 10), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (14, 15),
                        (15, 16),
                        (16, 17),
                        (16, 18),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Okay",
                        ",",
                        "so",
                        "January",
                        "25",
                        ",",
                        "2021",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(3, 5), (3, 7), (6, 7)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "6 p.m.",
                            "normalizedValue": "2021-01-21T18:00:00.000Z",
                        },
                        {
                            "label": "TIME",
                            "probability": 0.990385890007019,
                            "token": "6 p.m.",
                            "span": {"end": 6},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["6", "p.m", "."], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "January",
                        "25",
                        ",",
                        "2021",
                        ".",
                        "Got",
                        "it",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "time",
                        "?",
                        "6",
                        "p.m",
                        ".",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (0, 4),
                        (6, 7),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 13),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ",", "so", "18:00:00", "?", "yes"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (5, 6)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = ["make a reservation", "1/25/21", "yes", "6 p.m.", "yes"]

        target_responses = [
            ["make reservation", "your date?"],
            ["January 25, 2021"],
            ["January 25, 2021.", "your time?"],
            ["18:00:00"],
            ["18:00:00", "Is there anything else I can help you with today?"],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_retrieval_and_multiple_entities(
        self, mocked_info, mocked_func, mocked_api
    ):
        """
        Test situation where the user provide multiple entities in a single turn.
        The bot should handle them all, and if necessary, retrieve them from the
        history when needed.
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_entity_retrieval_and_multiple_entities.yaml",
            entity_path="./test_files/test_entity_retrieval"
            "_and_multiple_entities_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/email",
                            "token": "peter@hotmail.com",
                            "normalizedValue": "peter@hotmail.com",
                            "span": {"end": 17},
                        },
                        {
                            "label": "CARDINAL",
                            "probability": 0.6108670234680176,
                            "token": "94301",
                            "span": {"start": 64, "end": 69},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.47913044691085815,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"start": 64, "end": 69},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9137429594993591,
                    "sent": "i want to check order",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9137429594993591,
                        "sent": "i want to check order",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "check",
                        "order",
                        "status",
                        "for",
                        "email",
                        "peter",
                        "@",
                        "hotmail.com",
                        "and",
                        "zip",
                        "code",
                        "94301",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        "there",
                        ",",
                        "I",
                        "am",
                        "the",
                        "digital",
                        "assistant",
                        "for",
                        "Northern",
                        "Trail",
                        "Information",
                        "Center",
                        ".",
                        "What",
                        "can",
                        "I",
                        "do",
                        "for",
                        "you",
                        "?",
                        "check",
                        "order",
                        "status",
                        "for",
                        "email",
                        "peter",
                        "@",
                        "hotmail.com",
                        "and",
                        "zip",
                        "code",
                        "94301",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (4, 5),
                        (9, 13),
                        (16, 17),
                        (19, 20),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (25, 33),
                        (26, 29),
                        (26, 33),
                        (30, 32),
                        (30, 33),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9137429594993591,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Okay",
                        ",",
                        "so",
                        "K",
                        "I",
                        "N",
                        "G",
                        "S",
                        "I",
                        "at",
                        "salesforce",
                        "dot",
                        "com",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23)],
                        [(3, 4), (17, 18)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (18, 19),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (22, 38),
                        (28, 38),
                        (33, 34),
                        (33, 38),
                        (35, 38),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9812771677970886,
                    "sent": "query the climate",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9812771677970886,
                        "sent": "query the climate",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "the", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "One",
                        "moment",
                        "please",
                        ".",
                        "Your",
                        "order",
                        "status",
                        "is",
                        "10",
                        "pizza",
                        ",",
                        "placed",
                        "but",
                        "not",
                        "yet",
                        "shipped",
                        ".",
                        "That",
                        "is",
                        "all",
                        "the",
                        "information",
                        "that",
                        "I",
                        "have",
                        "on",
                        "your",
                        "order",
                        "status",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "the",
                        "weather",
                    ],
                    "predicted_clusters": [
                        [(7, 8), (29, 30), (40, 41)],
                        [(7, 10), (29, 32)],
                        [(26, 27), (37, 38)],
                    ],
                    "top_spans": [
                        (1, 2),
                        (1, 5),
                        (3, 5),
                        (7, 8),
                        (7, 10),
                        (11, 19),
                        (20, 21),
                        (22, 32),
                        (22, 43),
                        (26, 27),
                        (29, 30),
                        (29, 32),
                        (35, 43),
                        (37, 38),
                        (40, 41),
                        (42, 43),
                        (44, 45),
                        (45, 47),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9812771677970886,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.544232964515686,
                            "token": "94403",
                            "span": {"start": 30, "end": 35},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.10611212998628616,
                            "token": "code 94403",
                            "normalizedValue": (
                                "USPSBoxType:" "code|SubaddressIdentifier:94403"
                            ),
                            "span": {"start": 25, "end": 35},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8998427987098694,
                    "sent": "yes please",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8998427987098694,
                        "sent": "yes please",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "yes",
                        "please",
                        "check",
                        "for",
                        "zip",
                        "code",
                        "94403",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Weather",
                        "condition",
                        "is",
                        "clear",
                        "sky",
                        "at",
                        "Palo",
                        "Alto",
                        ",",
                        "94301",
                        ".",
                        "Your",
                        "request",
                        "is",
                        "completed",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "check",
                        "the",
                        "weather",
                        "for",
                        "another",
                        "zip",
                        "code",
                        "?",
                        "yes",
                        "please",
                        "check",
                        "for",
                        "zip",
                        "code",
                        "94403",
                    ],
                    "predicted_clusters": [[(9, 10), (25, 26), (31, 32)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 16),
                        (14, 16),
                        (20, 24),
                        (20, 27),
                        (25, 26),
                        (25, 27),
                        (28, 29),
                        (31, 32),
                        (32, 33),
                        (34, 35),
                        (35, 37),
                        (38, 41),
                        (44, 45),
                        (46, 49),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8998427987098694,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "Weather",
                        "condition",
                        "is",
                        "few",
                        "clouds",
                        "at",
                        "San",
                        "Mateo",
                        ",",
                        "94403",
                        ".",
                        "Your",
                        "request",
                        "is",
                        "completed",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "check",
                        "the",
                        "weather",
                        "for",
                        "another",
                        "zip",
                        "code",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [[(9, 10), (25, 26), (31, 32)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 16),
                        (14, 16),
                        (17, 27),
                        (20, 24),
                        (20, 27),
                        (25, 26),
                        (25, 27),
                        (28, 29),
                        (31, 32),
                        (34, 35),
                        (35, 37),
                        (38, 41),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(2, 10), (4, 5), (7, 8), (9, 10)],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is {} at {}, {}".format(
                    "clear sky", "Palo Alto", 94301
                ),
            ),
            resp(
                True,
                "Weather condition is {} at {}, {}".format(
                    "few clouds", "San Mateo", 94403
                ),
            ),
        ]

        mocked_api.side_effect = [
            resp(True, "Verified"),
            resp(True, "Verified"),
            resp(True, "10 pizza, placed but not yet shipped"),
        ]

        user_inputs = [
            "check order status for email peter@hotmail.com and zip code 94301",
            "yes",
            "check the weather",
            "yes please check for zip code 94403",
            "no",
            "no",
        ]

        target_responses = [
            [
                (
                    "Oh sure,"
                    " I'd be happy to help you check your order status. "
                    "First, I need to pull up your account."
                ),
                "Okay, so P E T E R at hotmail dot com?",
            ],
            [
                "One moment please.",
                "Your order status is 10 pizza, placed but not yet shipped.",
                "Is there anything else I can help you with today?",
            ],
            [
                "Oh sure, I'd be happy to help you check local weather.",
                "Weather condition is clear sky at Palo Alto, 94301.",
                "Your request has been completed.",
                "Would you like to check the weather for another zip code?",
            ],
            [
                "Oh sure, I'd be happy to help you check local weather.",
                "Weather condition is few clouds at San Mateo, 94403.",
                "Your request has been completed.",
                "Would you like to check the weather for another zip code?",
            ],
            ["Is there anything else I can help you with today?"],
            [
                "Sounds good. I'm glad I could help.",
                "Thanks for calling, and have a good one.",
            ],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_multiple_entity_types1(self, mocked_info, mocked_func):
        """
        This test goes along with test_multiple_entity_types2 below

        The methods test when there are multiple entity types in the configuration
        file(AP/Location and Zip code), the entity candidate of either type can serve
        as a valid input arg for data processing function (funcGetWeather).

        Test the case when the user answers location as 'san mateo', which is an
        AP/Location type
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_multiple_entity_types.yaml",
            entity_path="./test_files/test_multiple_entity_types_config.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9137429594993591,
                    "sent": "i want to check weather",
                },
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["agent", "response", "check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2)],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9137429594993591,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.9875142,
                            "token": "san mateo",
                            "span": {"end": 9},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9997781,
                            "token": "san mateo",
                            "normalizedValue": "PlaceName:san mateo",
                            "span": {"end": 9},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["san", "mateo"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["san", "mateo"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = [
            "i want to check weather",
            "san mateo",
        ]
        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is {} at {}, {}".format(
                    "few clouds", "San Mateo", 94403
                ),
            ),
        ]

        for user_input in user_inputs:
            dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)

        # The reason we can't use assert_called_once_with is that the argument to the
        # function (funcGetWeather) is not just the location but along with some other
        # args and kwargs. That is why we test this manually, with
        # mocked_func.call_args_list[0][0]; the first index for the function calls
        # and the second index for the location argument we are only interested in.
        self.assertEqual(mocked_func.call_count, 1)
        self.assertEqual(
            mocked_func.call_args_list[0][0],
            ({"location": (("PlaceName", "san mateo"),)},),
        )

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_multiple_entity_types2(self, mocked_info, mocked_func):
        """
        See test_multiple_entity_types1 for more details

        Test the case when the user answers location as '94403', which is a Zipcode
        type
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_multiple_entity_types.yaml",
            entity_path="./test_files/test_multiple_entity_types_config.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9137429594993591,
                    "sent": "i want to check weather",
                },
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["check", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["agent", "response", "check", "weather"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2)],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9137429594993591,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7607909,
                            "token": "94403",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.80640703,
                            "token": "94403",
                            "normalizedValue": "ZipCode:94403",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94403"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["agent", "response", "94403"],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = [
            "i want to check weather",
            "94403",
        ]
        mocked_func.side_effect = [
            resp(
                True,
                "Weather condition is {} at {}, {}".format(
                    "few clouds", "San Mateo", 94403
                ),
            ),
        ]

        for user_input in user_inputs:
            dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)

        # see test_multiple_entity_types1 for more details
        self.assertEqual(mocked_func.call_count, 1)
        self.assertEqual(
            mocked_func.call_args_list[0][0], ({"location": (("ZipCode", "94403"),)},)
        )

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_picklist_userutt(self, mocked_info):
        """
        We want to test two entity types: PICKLIST and USER_UTT
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_picklist_userutt_task.yaml",
            entity_path="./test_files/test_picklist_userutt_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "repeater",
                    "prob": 0.9924356341362,
                    "sent": "I want to test my repeater",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "repeater",
                        "prob": 0.9924356341362,
                        "sent": "I want to test my repeater",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "test", "my", "repeater"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["I", "want", "to", "test", "my", "repeater"],
                    "predicted_clusters": [[(0, 1), (4, 5)]],
                    "top_spans": [(0, 1), (4, 5)],
                },
                "final_intent": {
                    "intent": "repeater",
                    "prob": 0.9924356341362,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.809475302696228,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.809475302696228,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["a"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "test",
                        "your",
                        "repeater",
                        ".",
                        "What",
                        "is",
                        "your",
                        "repeater",
                        "'s",
                        "brand",
                        "?",
                        "A",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (16, 17)],
                        [(11, 13), (16, 19)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 13),
                        (16, 17),
                        (16, 19),
                        (16, 20),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.809475302696228,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["repeating", "is", "human", "'s", "nature"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "A",
                        ".",
                        "Got",
                        "it",
                        ".",
                        "Just",
                        "say",
                        "something",
                        ",",
                        "please",
                        ".",
                        "repeating",
                        "is",
                        "human",
                        "'s",
                        "nature",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4), (6, 7), (7, 8), (11, 12), (13, 15), (13, 16)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9785935878753662,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "repeating",
                        "is",
                        "human",
                        "'s",
                        "nature",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "let",
                        "it",
                        "repeat",
                        "again",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [[(6, 7), (13, 14)], [(6, 8), (17, 18)]],
                    "top_spans": [
                        (0, 1),
                        (2, 4),
                        (2, 5),
                        (6, 7),
                        (6, 8),
                        (10, 11),
                        (13, 14),
                        (17, 18),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9785935878753662,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.9902869462966919,
                            "token": "AAPL",
                            "span": {"end": 4},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7697403430938721,
                    "sent": "Sure",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7697403430938721,
                        "sent": "Sure",
                    }
                ],
                "negation": {"wordlist": ["aapl"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "test",
                        "your",
                        "repeater",
                        ".",
                        "What",
                        "is",
                        "your",
                        "repeater",
                        "'s",
                        "brand",
                        "?",
                        "AAPL",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (16, 17)],
                        [(11, 13), (16, 19)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 13),
                        (16, 17),
                        (16, 19),
                        (21, 22),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7697403430938721,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "repeater",
                    "prob": 0.988000214099884,
                    "sent": "I like my repeater",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "repeater",
                        "prob": 0.988000214099884,
                        "sent": "I like my repeater",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "like", "to", "repeat"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "AAPL",
                        ".",
                        "Got",
                        "it",
                        ".",
                        "Just",
                        "say",
                        "something",
                        ",",
                        "please",
                        ".",
                        "I",
                        "like",
                        "to",
                        "repeat",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2), (3, 4), (6, 7), (7, 8), (11, 12), (14, 15)],
                },
                "final_intent": {
                    "intent": "repeater",
                    "prob": 0.988000214099884,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9758957028388977,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "I",
                        "like",
                        "to",
                        "repeat",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "let",
                        "it",
                        "repeat",
                        "again",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [[(5, 6), (12, 13)], [(5, 7), (16, 17)]],
                    "top_spans": [
                        (0, 1),
                        (3, 4),
                        (5, 6),
                        (5, 7),
                        (9, 10),
                        (12, 13),
                        (15, 16),
                        (16, 17),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9758957028388977,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "I want to test my repeater",
            "A",
            "repeating is human's nature",
            "yes",
            "AAPL",
            "I like to repeat",
            "no",
        ]

        target_responses = [
            (
                "Oh sure, I'd be happy to help you test your repeater. "
                "What is your repeater's brand?"
            ),
            "A. Got it. Just say something, please.",
            (
                "repeating is human's nature. Your request has been completed. "
                "Would you like to let it repeat again?"
            ),
            (
                "Oh sure, I'd be happy to help you test your repeater. "
                "What is your repeater's brand?"
            ),
            "AAPL. Got it. Just say something, please.",
            (
                "I like to repeat. Your request has been completed. "
                "Would you like to let it repeat again?"
            ),
            "Is there anything else I can help you with today?",
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            self.assertEqual(res, target)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_picklist_nonstring(self, mocked_info):
        """
        We test picklist where some choices are not string types
        """

        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_picklist_retail_tasks.yaml",
            entity_path="./test_files/test_picklist_retail_entities.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "get_refund",
                    "prob": 0.9562110304832458,
                    "sent": "get a refund",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "get_refund",
                        "prob": 0.9562110304832458,
                        "sent": "get a refund",
                    }
                ],
                "negation": {"wordlist": ["get", "refund"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["get", "refund"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "get_refund",
                    "prob": 0.9562110304832458,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.6494267,
                            "token": "123-456-789",
                            "span": {"end": 11},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.99263716,
                            "token": "123-456-789",
                            "normalizedValue": "AddressNumber:123-456-789",
                            "span": {"end": 11},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["123-456-789"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["123-456-789"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7635553,
                            "token": "3",
                            "span": {"end": 1},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["3"], "triplets": [(-1, -1, -1)]},
                "coref": {"words": ["3"], "predicted_clusters": [], "top_spans": []},
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "get_refund",
                    "prob": 0.6528638005256653,
                    "sent": "get a refund",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "get_refund",
                        "prob": 0.6528638005256653,
                        "sent": "get a refund",
                    }
                ],
                "negation": {
                    "wordlist": ["credit", "card"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["credit", "card"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "get_refund",
                    "prob": 0.6528638005256653,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "get refund",
            "123-456-789",
            "3",
            "credit card",
        ]

        target_responses = [
            (
                "Oh sure, I'd be happy to help you get a refund for your order. "
                "Please provide your order id for your order details."
            ),
            (
                "One moment please. Here are the details of your order: 123-456-789. "
                "What is the reason that you decided to cancel your order? "
                "1) It took too long to deliver. "
                "2) I no longer needed the item. "
                "3) Something else."
            ),
            (
                "One moment please. Here are the details of your order: 3. "
                "How would you like the refund? "
                "In store credit or returned to the credit card on which "
                "you made the purchase?"
            ),
            (
                "One moment please. Here are the details of your order: credit card. "
                "Your request has been completed. "
                "Would you like to get a refund for your order again?"
            ),
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            self.assertEqual(res, target)

    @patch("Converse.entity_backend.entity_functions.create_appointment")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_finish_function_success(self, mocked_info, mocked_func):
        """
        Test task entity info collection and task finish function. In this unit
        test, the entity info was collected in dialogue context, and cleared
        after successful completion of task finish function.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_finish_function_task_config.yaml",
            entity_path="./test_files/test_task_finish_function_entity_config.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "health_appointment",
                    "prob": 0.9682004451751709,
                    "sent": "I want to see a doctor",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "health_appointment",
                        "prob": 0.9682004451751709,
                        "sent": "I want to see a doctor",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "see", "a", "doctor"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["I", "want", "to", "see", "a", "doctor"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (4, 6)],
                },
                "final_intent": {
                    "intent": "health_appointment",
                    "prob": 0.9682004451751709,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "Apr 1, 2021",
                            "normalizedValue": "2021-04-01T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.9685498,
                            "token": "Apr 1, 2021",
                            "span": {"end": 11},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["apr", "1", ",", "2021"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "make",
                        "an",
                        "appointment",
                        "at",
                        "Stanford",
                        "Health",
                        "Care",
                        ".",
                        "What",
                        "'s",
                        "your",
                        "preferred",
                        "date",
                        "for",
                        "the",
                        "appointment",
                        "?",
                        "Apr",
                        "1",
                        ",",
                        "2021",
                    ],
                    "predicted_clusters": [[(9, 10), (20, 21)], [(11, 17), (24, 26)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 17),
                        (14, 17),
                        (20, 21),
                        (20, 26),
                        (24, 26),
                        (27, 29),
                        (27, 31),
                        (30, 31),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "10 am",
                            "normalizedValue": "2021-04-07T10:00:00.000Z",
                        },
                        {
                            "label": "TIME",
                            "probability": 0.9147723,
                            "token": "10 am",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7575251460075378,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7575251460075378,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["10", "am"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ".", "At", "what", "time", "?", "10", "am"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (6, 7), (6, 8)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7575251460075378,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.9349234,
                            "token": "Tom",
                            "span": {"end": 3},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["tom"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "What",
                        "is",
                        "your",
                        "doctor",
                        "name",
                        "?",
                        "Tom",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (5, 6), (5, 8), (9, 10)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_func.return_value = resp(True, msg="Appointment created.")

        user_inputs = ["I want to see a doctor", "Apr 1, 2021", "10 am", "Tom"]

        target_dicts = [
            {},
            {"appt_date": datetime.date(2021, 4, 1)},
            {
                "appt_date": datetime.date(2021, 4, 1),
                "appt_time": datetime.time(10, 0),
            },
            {
                "appt_date": datetime.date(2021, 4, 1),
                "appt_time": datetime.time(10, 0),
                "doctor_name": "Tom",
            },
        ]

        target_responses = [
            "What's your preferred date for the appointment?",
            "At what time?",
            "your doctor name?",
            "I have booked an appointment for you.",
        ]

        for user_input, entity_dict, target_response in zip(
            user_inputs, target_dicts, target_responses
        ):

            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            self.assertDictEqual(ctx.collected_entities, entity_dict)
            self.assertIn(target_response, res)

    @patch("Converse.entity_backend.entity_functions.create_appointment")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_finish_function_fail(self, mocked_info, mocked_func):
        """
        Test task entity info collection and task finish function. In this unit
        test, the entity info was collected in dialogue context, but not cleared
        after task finish function execution failed.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_task_finish_function_task_config.yaml",
            entity_path="./test_files/test_task_finish_function_entity_config.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "health_appointment",
                    "prob": 0.9682004451751709,
                    "sent": "I want to see a doctor",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "health_appointment",
                        "prob": 0.9682004451751709,
                        "sent": "I want to see a doctor",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "see", "a", "doctor"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["I", "want", "to", "see", "a", "doctor"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (4, 6)],
                },
                "final_intent": {
                    "intent": "health_appointment",
                    "prob": 0.9682004451751709,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "Apr 1, 2021",
                            "normalizedValue": "2021-04-01T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.9685498,
                            "token": "Apr 1, 2021",
                            "span": {"end": 11},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["apr", "1", ",", "2021"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "make",
                        "an",
                        "appointment",
                        "at",
                        "Stanford",
                        "Health",
                        "Care",
                        ".",
                        "What",
                        "'s",
                        "your",
                        "preferred",
                        "date",
                        "for",
                        "the",
                        "appointment",
                        "?",
                        "Apr",
                        "1",
                        ",",
                        "2021",
                    ],
                    "predicted_clusters": [[(9, 10), (20, 21)], [(11, 17), (24, 26)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 17),
                        (14, 17),
                        (20, 21),
                        (20, 26),
                        (24, 26),
                        (27, 29),
                        (27, 31),
                        (30, 31),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "10 am",
                            "normalizedValue": "2021-04-07T10:00:00.000Z",
                        },
                        {
                            "label": "TIME",
                            "probability": 0.9147723,
                            "token": "10 am",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7575251460075378,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7575251460075378,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["10", "am"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ".", "At", "what", "time", "?", "10", "am"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (6, 7), (6, 8)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7575251460075378,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.9349234,
                            "token": "Tom",
                            "span": {"end": 3},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["tom"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "What",
                        "is",
                        "your",
                        "doctor",
                        "name",
                        "?",
                        "Tom",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (5, 6), (5, 8), (9, 10)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_func.return_value = resp(False, msg="Failed to create appointment.")

        user_inputs = ["I want to see a doctor", "Apr 1, 2021", "10 am", "Tom"]

        target_dicts = [
            {},
            {"appt_date": datetime.date(2021, 4, 1)},
            {
                "appt_date": datetime.date(2021, 4, 1),
                "appt_time": datetime.time(10, 0),
            },
            {
                "appt_date": datetime.date(2021, 4, 1),
                "appt_time": datetime.time(10, 0),
                "doctor_name": "Tom",
            },
        ]

        target_responses = [
            "What's your preferred date for the appointment?",
            "At what time?",
            "your doctor name?",
            "Sorry, I can't help you book an appointment.",
        ]

        for user_input, entity_dict, target_response in zip(
            user_inputs, target_dicts, target_responses
        ):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            self.assertDictEqual(ctx.collected_entities, entity_dict)
            self.assertIn(target_response, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_task_finish_function_fail_test(self, mocked_info, mocked_func):
        """
        Test task entity info collection and task finish function. In this unit
        test, the entity info was collected in dialogue context, but not cleared
        after task finish function execution failed.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_text_bot_task.yaml",
            entity_path="./test_files/test_text_bot_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "sent": "check order status",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.928551435470581,
                        "sent": "check order status",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 3)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.928551435470581,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/email",
                            "token": "random@gmail.com",
                            "normalizedValue": "random@gmail.com",
                        },
                        {
                            "label": "PERSON",
                            "probability": 0.9008819460868835,
                            "token": "random@gmail.com",
                            "span": {"end": 16},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9391730427742004,
                    "sent": "Not exactly",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9391730427742004,
                        "sent": "Not exactly",
                    }
                ],
                "negation": {
                    "wordlist": ["random", "@", "gmail.com"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "What",
                        "is",
                        "your",
                        "email",
                        "address",
                        "?",
                        "random",
                        "@",
                        "gmail.com",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (27, 28)],
                        [(3, 4), (17, 18)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (27, 28),
                        (27, 30),
                        (31, 34),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9391730427742004,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9752330780029297,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9752330780029297,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Okay",
                        ",",
                        "so",
                        "random",
                        "@",
                        "gmail.com",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (3, 6), (5, 6)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9752330780029297,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.595866858959198,
                            "token": "99999",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.8893020153045654,
                            "token": "99999",
                            "normalizedValue": "AddressNumber:99999",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["99999"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "I",
                        "am",
                        "sorry",
                        ",",
                        "but",
                        "I",
                        "could",
                        "not",
                        "recognize",
                        "your",
                        "email_address",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "99999",
                    ],
                    "predicted_clusters": [[(0, 1), (5, 6)], [(9, 10), (14, 15)]],
                    "top_spans": [
                        (0, 1),
                        (5, 6),
                        (9, 10),
                        (9, 11),
                        (14, 15),
                        (14, 17),
                        (18, 19),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_func.return_value = resp(False, msg="Verify failed")

        user_inputs = ["check order status", "random@gmail.com", "yes", "99999"]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you check your order status.",
                "First, I need to pull up your account.",
                "your email address?",
            ],
            ["Okay, so random@gmail.com?"],
            [
                "I am sorry, but I could not recognize your email_address.",
                "your zip code?",
            ],
            [
                "I am sorry, but I could not recognize your zip_code.",
                "I couldn't help you with your request.",
                "Let me forward this case to one of our professional agents.",
                "Please wait for 5 minutes.",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_faq_inside_of_a_task(self, mocked_info):
        """
        Test FAQ config.
        The orchestrator should pick up FAQ config from the tasks.yaml
        And FAQ can be inserted anywhere in an conversation
        """
        dm = Orchestrator(
            response_path="./test_files/test_faq_response_template.yaml",
            task_path="./test_files/test_faq_tasks.yaml",
            entity_path="./test_files/test_faq_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "book_a_flight",
                    "prob": 0.9521209001541138,
                    "sent": "book a flight",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "book_a_flight",
                        "prob": 0.9521209001541138,
                        "sent": "book a flight",
                    }
                ],
                "negation": {
                    "wordlist": ["book", "a", "flight"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["book", "a", "flight"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "book_a_flight",
                    "prob": 0.9521209001541138,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.9668965935707092,
                            "token": "san francisco",
                            "span": {"end": 13},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9511712789535522,
                            "token": "san francisco",
                            "normalizedValue": "PlaceName:san francisco",
                            "span": {"end": 13},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["san", "francisco"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "book",
                        "a",
                        "flight",
                        ".",
                        "Where",
                        "is",
                        "the",
                        "origin",
                        "?",
                        "san",
                        "francisco",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 18),
                        (16, 18),
                        (19, 21),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.9719483256340027,
                            "token": "Salesforce AI research team?",
                            "span": {"start": 31, "end": 59},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9674779772758484,
                    "sent": "Could you tell me about Salesforce AI research team?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "learn_about_salesforce_AI_research",
                        "prob": 0.9674779772758484,
                        "sent": "Could you tell me about Salesforce AI research team?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "could",
                        "you",
                        "please",
                        "tell",
                        "me",
                        "about",
                        "salesforce",
                        "ai",
                        "research",
                        "team",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Where",
                        "is",
                        "the",
                        "destination",
                        "?",
                        "could",
                        "you",
                        "please",
                        "tell",
                        "me",
                        "about",
                        "Salesforce",
                        "AI",
                        "research",
                        "team",
                        "?",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (1, 2),
                        (5, 7),
                        (9, 10),
                        (11, 12),
                        (12, 13),
                        (14, 18),
                        (15, 16),
                    ],
                },
                "final_intent": {
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9674779772758484,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.8831698894500732,
                            "token": "San Diego",
                            "span": {"end": 9},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9728764891624451,
                            "token": "San Diego",
                            "normalizedValue": "PlaceName:San Diego",
                            "span": {"end": 9},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["san", "diego"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "could",
                        "you",
                        "please",
                        "tell",
                        "me",
                        "about",
                        "Salesforce",
                        "AI",
                        "research",
                        "team",
                        "?",
                        "San",
                        "Diego",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (4, 5), (6, 10), (7, 8), (11, 13)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = [
            "book a flight",
            "san francisco",
            "could you please tell me about Salesforce AI research team?",
            "San Diego",
        ]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you book a flight.",
                "Where is the origin?",
            ],
            ["Where is the destination?"],
            [
                "OK, here's what I found - https://einstein.ai/mission.",
                "Where is the destination?",
            ],
            [
                "When will your trip start?",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_faq_outside_of_a_task(self, mocked_info):
        """
        Test FAQ config.
        The orchestrator should pick up FAQ config from the tasks.yaml
        """
        dm = Orchestrator(
            response_path="./test_files/test_faq_response_template.yaml",
            task_path="./test_files/test_faq_tasks.yaml",
            entity_path="./test_files/test_faq_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.963439404964447,
                            "token": "Salesforce AI research team?",
                            "span": {"start": 24, "end": 52},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9599077701568604,
                    "sent": "Could you tell me about Salesforce AI research team?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "learn_about_salesforce_AI_research",
                        "prob": 0.9599077701568604,
                        "sent": "Could you tell me about Salesforce AI research team?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "could",
                        "you",
                        "tell",
                        "me",
                        "about",
                        "salesforce",
                        "ai",
                        "research",
                        "team",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "could",
                        "you",
                        "tell",
                        "me",
                        "about",
                        "Salesforce",
                        "AI",
                        "research",
                        "team",
                        "?",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (3, 4), (5, 9), (6, 7)],
                },
                "final_intent": {
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9599077701568604,
                    "uncertain": False,
                },
            }
        ]
        user_inputs = ["could you please tell me about Salesforce AI research team?"]

        target_responses = [
            [
                "OK, here's what I found - https://einstein.ai/mission.",
                "Can I assist you with anything else?",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_faq_exact_match_inside_of_a_task(self, mocked_info):
        """
        Test FAQ config.
        The orchestrator should pick up FAQ config from the tasks.yaml
        And FAQ can be inserted anywhere in an conversation
        """
        dm = Orchestrator(
            response_path="./test_files/test_faq_response_template.yaml",
            task_path="./test_files/test_faq_tasks.yaml",
            entity_path="./test_files/test_faq_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "book_a_flight",
                    "prob": 0.9521209001541138,
                    "sent": "book a flight",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "book_a_flight",
                        "prob": 0.9521209001541138,
                        "sent": "book a flight",
                    }
                ],
                "negation": {
                    "wordlist": ["book", "a", "flight"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["book", "a", "flight"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "book_a_flight",
                    "prob": 0.9521209001541138,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.9668965935707092,
                            "token": "san francisco",
                            "span": {"end": 13},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9511712789535522,
                            "token": "san francisco",
                            "normalizedValue": "PlaceName:san francisco",
                            "span": {"end": 13},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["san", "francisco"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "book",
                        "a",
                        "flight",
                        ".",
                        "Where",
                        "is",
                        "the",
                        "origin",
                        "?",
                        "san",
                        "francisco",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 18),
                        (16, 18),
                        (19, 21),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.5890876650810242,
                            "token": "Salesforce",
                            "span": {"start": 38, "end": 48},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.8897483348846436,
                    "sent": "Could you tell me about Salesforce AI research team?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "learn_about_salesforce_AI_research",
                        "prob": 0.8897483348846436,
                        "sent": "Could you tell me about Salesforce AI research team?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "where",
                        "can",
                        "i",
                        "find",
                        "job",
                        "opportunities",
                        "in",
                        "salesforce",
                        "research",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Okay",
                        ".",
                        "Where",
                        "is",
                        "the",
                        "destination",
                        "?",
                        "where",
                        "can",
                        "I",
                        "find",
                        "job",
                        "opportunities",
                        "in",
                        "Salesforce",
                        "research",
                        "?",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (4, 6),
                        (9, 10),
                        (10, 11),
                        (11, 16),
                        (14, 15),
                        (14, 16),
                    ],
                },
                "final_intent": {
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.8897483348846436,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.8831698894500732,
                            "token": "San Diego",
                            "span": {"end": 9},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9728764891624451,
                            "token": "San Diego",
                            "normalizedValue": "PlaceName:San Diego",
                            "span": {"end": 9},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["san", "diego"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "where",
                        "can",
                        "I",
                        "find",
                        "job",
                        "opportunities",
                        "in",
                        "Salesforce",
                        "research",
                        "?",
                        "San",
                        "Diego",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3), (7, 8), (7, 9), (10, 12)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        user_inputs = [
            "book a flight",
            "san francisco",
            "where can I find job opportunities in Salesforce research?",
            "San Diego",
        ]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you book a flight.",
                "Where is the origin?",
            ],
            ["Where is the destination?"],
            [
                "Thanks for your interest! Please see https://einstein.ai/career",
                "Where is the destination?",
            ],
            [
                "When will your trip start?",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_faq_exact_match_outside_of_a_task(self, mocked_info):
        """
        Test FAQ config.
        The orchestrator should pick up FAQ config from the tasks.yaml
        """
        dm = Orchestrator(
            response_path="./test_files/test_faq_response_template.yaml",
            task_path="./test_files/test_faq_tasks.yaml",
            entity_path="./test_files/test_faq_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.5890876650810242,
                            "token": "Salesforce",
                            "span": {"start": 38, "end": 48},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.8897483348846436,
                    "sent": "Could you tell me about Salesforce AI research team?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "learn_about_salesforce_AI_research",
                        "prob": 0.8897483348846436,
                        "sent": "Could you tell me about Salesforce AI research team?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "where",
                        "can",
                        "i",
                        "find",
                        "job",
                        "opportunities",
                        "in",
                        "salesforce",
                        "research",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "where",
                        "can",
                        "I",
                        "find",
                        "job",
                        "opportunities",
                        "in",
                        "Salesforce",
                        "research",
                        "?",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3), (4, 9), (7, 8), (7, 9)],
                },
                "final_intent": {
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.8897483348846436,
                    "uncertain": False,
                },
            }
        ]
        user_inputs = ["where can I find job opportunities in Salesforce research?"]

        target_responses = [
            [
                "Thanks for your interest! Please see https://einstein.ai/career",
                "Can I assist you with anything else?",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.entity_backend.entity_functions.funcGetWeather")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_additional_entity_function(self, mocked_info, mocked_func):
        """
        Test additional entity function.
        Besides the default entity functions, the system should be able to
        load additional entity functions from user-specified path. So the dialogue
        state manager can use all the entity functions from both files.
        This function test 3 cases:
        1. There're duplicated functions from the default entity functions
            and the additional entity functions. The additional entity function
            should has a higher priority and overrides the default one.
        2. The desired function is from the default entity functions.
        3. The desired function is from the additional entity functions.
        """
        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8190558552742004,
                    "sent": "convert inch",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "convert_inch_to_cm",
                        "prob": 0.8190558552742004,
                        "sent": "convert inch",
                    }
                ],
                "negation": {
                    "wordlist": ["convert", "inch", "to", "cm"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["convert", "inch", "to", "cm"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8190558552742004,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8111811280250549,
                            "token": "5",
                            "span": {"end": 1},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.5895622968673706,
                            "token": "5",
                            "normalizedValue": "AddressNumber:5",
                            "span": {"end": 1},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["5"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "convert",
                        "inch",
                        "to",
                        "centimeter",
                        ".",
                        "What",
                        "is",
                        "your",
                        "inch",
                        "?",
                        "5",
                    ],
                    "predicted_clusters": [[(9, 10), (17, 18)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 14),
                        (17, 18),
                        (17, 19),
                        (20, 21),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9587552547454834,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9587552547454834,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "the", "local", "weather"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "The",
                        "Inch",
                        "to",
                        "Cm",
                        "function",
                        "is",
                        "from",
                        "the",
                        "additional",
                        "functions",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "check",
                        "the",
                        "local",
                        "weather",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 5),
                        (1, 4),
                        (7, 10),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (24, 25),
                        (26, 27),
                        (28, 29),
                        (29, 32),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9587552547454834,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9981836676597595,
                            "token": "94401",
                            "normalizedValue": "ZipCode:94401",
                            "span": {"start": 15, "end": 20},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["my", "zip", "code", "is", "94401"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "local",
                        "weather",
                        ".",
                        "What",
                        "is",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "my",
                        "zip",
                        "code",
                        "is",
                        "94401",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (16, 17), (20, 21)],
                        [(16, 19), (20, 23)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (16, 17),
                        (16, 19),
                        (20, 21),
                        (20, 23),
                        (24, 25),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_TV_plan_price",
                    "prob": 0.9094142317771912,
                    "sent": "tv plan",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_TV_plan_price",
                        "prob": 0.9094142317771912,
                        "sent": "tv plan",
                    }
                ],
                "negation": {"wordlist": ["tv", "plan"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Weather",
                        "condition",
                        "is",
                        "few",
                        "clouds",
                        "at",
                        "San",
                        "Mateo",
                        ",",
                        "94401",
                        ".",
                        "Your",
                        "request",
                        "has",
                        "been",
                        "completed",
                        ".",
                        "Is",
                        "there",
                        "anything",
                        "else",
                        "I",
                        "can",
                        "help",
                        "you",
                        "with",
                        "today",
                        "?",
                        "tv",
                        "plan",
                    ],
                    "predicted_clusters": [[(11, 12), (24, 25)]],
                    "top_spans": [
                        (0, 2),
                        (3, 13),
                        (6, 10),
                        (6, 13),
                        (11, 12),
                        (11, 13),
                        (15, 16),
                        (19, 27),
                        (21, 22),
                        (24, 25),
                        (26, 27),
                        (28, 30),
                    ],
                },
                "final_intent": {
                    "intent": "check_TV_plan_price",
                    "prob": 0.9094142317771912,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.9554393291473389,
                            "token": "hulu",
                            "span": {"end": 4},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["hulu"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "tv",
                        "plan",
                        "price",
                        ".",
                        "What",
                        "is",
                        "your",
                        "new",
                        "tv",
                        "plan",
                        "?",
                        "hulu",
                    ],
                    "predicted_clusters": [[(9, 10), (17, 18)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 14),
                        (17, 18),
                        (17, 21),
                        (22, 23),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]
        mocked_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format("clear sky", "San Mateo", 94401),
        )

        dm = Orchestrator(
            task_path="test_files/test_additional_entity_functions_tasks.yaml",
            entity_path="test_files/test_entity_config.yaml",
            entity_function_path="test_files/additional_entity_function.py",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        user_inputs = [
            "convert inch to cm",
            "5",
            "check the local weather",
            "my zip code is 94401",
            "tv plan",
            "hulu",
        ]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you convert inch to centimeter.",
                "your inch?",
            ],
            [
                "The Inch to Cm function is from the additional functions.",
            ],
            [
                "Oh sure, I'd be happy to help you check local weather.",
                "your zip code?",
            ],
            [
                "Weather condition is clear sky at San Mateo, 94401.",
            ],
            [
                "Oh sure, I'd be happy to help you check tv plan price.",
                "your new tv plan?",
            ],
            [
                "This is the return value of a test additional function.",
            ],
        ]

        for user_input, target_response in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target_response:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_use_merged_task_entity_config_file(self, mocked_info, mocked_func):
        """
        Unit test for online shopping example with merged task entity config file.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_merged_task_entity.yaml",
            entity_path="./test_files/test_merged_task_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9300524592399597,
                    "sent": "yes please",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9300524592399597,
                        "sent": "yes please",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "..."],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["I", "want", "to", "..."],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9300524592399597,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_order",
                    "prob": 0.9539812207221985,
                    "sent": "i want to check order",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_order",
                        "prob": 0.9539812207221985,
                        "sent": "i want to check order",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "check", "order", "status"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "I",
                        "am",
                        "sorry",
                        "that",
                        "I",
                        "could",
                        "n't",
                        "understand",
                        "what",
                        "you",
                        "said",
                        ".",
                        "Here",
                        "'s",
                        "what",
                        "I",
                        "can",
                        "do",
                        ":",
                        "1.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "2.",
                        "check",
                        "your",
                        "order",
                        "status",
                        "You",
                        "can",
                        "ask",
                        "me",
                        "to",
                        "do",
                        "these",
                        "tasks",
                        ".",
                        "I",
                        "want",
                        "to",
                        "check",
                        "order",
                        "status",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (23, 24), (27, 28), (30, 31), (40, 41)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (23, 24),
                        (23, 25),
                        (23, 30),
                        (26, 27),
                        (27, 28),
                        (27, 30),
                        (30, 31),
                        (32, 33),
                        (34, 35),
                        (37, 39),
                        (40, 41),
                        (43, 44),
                        (44, 46),
                    ],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9539812207221985,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9813255071640015,
                    "sent": "I dont know",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9813255071640015,
                        "sent": "I dont know",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "do", "n't", "know"],
                    "triplets": [(2, 3, 4)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "your",
                        "order",
                        "status",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "pull",
                        "up",
                        "your",
                        "account",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "email",
                        "address",
                        "?",
                        "I",
                        "do",
                        "n't",
                        "know",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (28, 29), (32, 33)],
                        [(3, 4), (17, 18), (26, 27)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 14),
                        (17, 18),
                        (20, 21),
                        (22, 23),
                        (22, 24),
                        (26, 27),
                        (27, 28),
                        (28, 29),
                        (28, 31),
                        (32, 33),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9813255071640015,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.41351426,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.85583746,
                            "token": "94301",
                            "normalizedValue": "ZipCode:94301",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94301"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "I",
                        "am",
                        "sorry",
                        ",",
                        "but",
                        "I",
                        "could",
                        "not",
                        "recognize",
                        "your",
                        "email_address",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "zip",
                        "code",
                        "?",
                        "94301",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (5, 6), (13, 14)],
                        [(9, 10), (15, 16)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (5, 6),
                        (9, 10),
                        (9, 11),
                        (13, 14),
                        (15, 16),
                        (15, 18),
                        (19, 20),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.82540727,
                            "token": "1",
                            "span": {"end": 1},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.46774104,
                            "token": "1",
                            "normalizedValue": "AddressNumber:1",
                            "span": {"end": 1},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8429444432258606,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8429444432258606,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["1"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Okay",
                        ".",
                        "I",
                        "have",
                        "verified",
                        "your",
                        "identity",
                        ".",
                        "Please",
                        "provide",
                        "your",
                        "order",
                        "id",
                        "for",
                        "your",
                        "order",
                        "status",
                        ".",
                        "1",
                    ],
                    "predicted_clusters": [[(5, 6), (10, 11), (14, 15)]],
                    "top_spans": [
                        (2, 3),
                        (4, 5),
                        (5, 6),
                        (5, 7),
                        (10, 11),
                        (14, 15),
                        (14, 17),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8429444432258606,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "update_order",
                    "prob": 0.9792688488960266,
                    "sent": "Please add another item to my order",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "update_order",
                        "prob": 0.9792688488960266,
                        "sent": "Please add another item to my order",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "add", "more", "to", "my", "order"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "One",
                        "moment",
                        "please",
                        ".",
                        "Your",
                        "order",
                        "status",
                        "is",
                        "placed",
                        "but",
                        "not",
                        "yet",
                        "shipped",
                        ".",
                        "That",
                        "is",
                        "all",
                        "the",
                        "information",
                        "that",
                        "I",
                        "have",
                        "on",
                        "your",
                        "order",
                        "status",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "check",
                        "the",
                        "status",
                        "of",
                        "another",
                        "order",
                        "?",
                        "I",
                        "want",
                        "to",
                        "add",
                        "more",
                        "to",
                        "my",
                        "order",
                    ],
                    "predicted_clusters": [
                        [(4, 5), (23, 24), (28, 29), (38, 39), (44, 45)],
                        [(4, 7), (23, 26)],
                    ],
                    "top_spans": [
                        (0, 2),
                        (4, 5),
                        (4, 7),
                        (8, 9),
                        (14, 15),
                        (16, 26),
                        (16, 37),
                        (20, 21),
                        (23, 24),
                        (23, 26),
                        (28, 29),
                        (31, 32),
                        (32, 37),
                        (35, 37),
                        (38, 39),
                        (41, 42),
                        (44, 45),
                        (44, 46),
                    ],
                },
                "final_intent": {
                    "intent": "update_order",
                    "prob": 0.9792688488960266,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9752330780029297,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9752330780029297,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["yes"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        ".",
                        "Your",
                        "oid",
                        "is",
                        "1",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [[(9, 10), (13, 14), (16, 17)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (13, 14),
                        (13, 15),
                        (16, 17),
                        (16, 18),
                        (19, 23),
                        (22, 23),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9752330780029297,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7794404,
                            "token": "15",
                            "span": {"end": 2},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.52841675,
                            "token": "15",
                            "normalizedValue": "AddressNumber:15",
                            "span": {"end": 2},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["15"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Sure",
                        ".",
                        "How",
                        "many",
                        "do",
                        "you",
                        "want",
                        "to",
                        "add",
                        "?",
                        "15",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4), (5, 6), (6, 7), (10, 11)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.9702200293540955,
                    "sent": "correct",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.9702200293540955,
                        "sent": "correct",
                    }
                ],
                "negation": {"wordlist": ["correct"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["Okay", ",", "so", "15", "?", "correct"],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4), (5, 6)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9702200293540955,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.973708987236023,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no"], "triplets": [(0, 1, 1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Now",
                        "you",
                        "have",
                        "ordered",
                        "25",
                        "pieces",
                        ".",
                        "Your",
                        "order",
                        "has",
                        "been",
                        "updated",
                        ".",
                        "Would",
                        "you",
                        "like",
                        "to",
                        "add",
                        "more",
                        "items",
                        "to",
                        "your",
                        "order",
                        "?",
                        "no",
                    ],
                    "predicted_clusters": [
                        [(4, 5), (10, 11), (17, 18), (24, 25)],
                        [(10, 12), (24, 26)],
                    ],
                    "top_spans": [
                        (1, 2),
                        (4, 5),
                        (6, 7),
                        (7, 9),
                        (10, 11),
                        (10, 12),
                        (14, 15),
                        (17, 18),
                        (21, 23),
                        (24, 25),
                        (24, 26),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.973708987236023,
                    "uncertain": False,
                },
            },
        ]
        mocked_func.side_effect = [
            {"success": True, "msg": "Verified"},
            {"success": True, "msg": "placed but not yet shipped"},
            {"success": True, "msg": "25"},
        ]

        user_inputs = [
            "I want to ...",
            "I want to check order status",
            "I don't know",
            "94301",
            "1",
            "I want to add more to my order",
            "yes",
            "15",
            "correct" "no",
        ]
        target_responses = [
            [
                "I am sorry that I couldn't understand what you said.",
                "Here's what I can do: \n",
                "add more to your order\n",
                "check your order status\n",
                "You can ask me to do these tasks.",
            ],
            [
                "Oh sure, I'd be happy to help you check your order status.",
                "First, I need to pull up your account. ",
                "your email address?",
            ],
            [
                "I am sorry, but I could not recognize your email_address.",
                "your zip code?",
            ],
            [
                "I have verified your identity.",
                "Please provide your order id for your order status.",
            ],
            [
                "One moment please.",
                "Your order status is placed but not yet shipped.",
                "That is all the information that I have on your order status. ",
                "Would you like to check the status of another order?",
            ],
            [
                "Oh sure, I'd be happy to help you add more to your order.",
                "Your oid is 1. Is that correct?",
            ],
            ["Sure. How many do you want to add?"],
            ["Okay, so 15?"],
            [
                "Got it. Now you have ordered 25 pieces.",
                "Your order has been updated.",
                "Would you like to add more items to your order?",
            ],
            ["Is there anything else I can help you with today?"],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_entity_retrieval_with_negation_and_forget(self, mocked_info, mocked_func):
        """
        Unit test for entity retrieval with forget setting and remove multiple candidates.
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./test_files/test_entity_retrieval_with_forget_tasks.yaml",
            entity_path="./test_files/test_entity_retrieval_with_forget_entity.yaml",
            info_path="./Converse/bot_configs/dial_info_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "test_task",
                    "prob": 0.9098727107048035,
                    "sent": "check information",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "test_task",
                        "prob": 0.9098727107048035,
                        "sent": "check information",
                    }
                ],
                "negation": {"wordlist": ["check", "info"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["check", "info"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {
                    "intent": "test_task",
                    "prob": 0.9098727107048035,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "last Tuesday",
                            "normalizedValue": "2021-11-02T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8798590898513794,
                            "token": "last Tuesday",
                            "span": {"end": 12},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["last", "tuesday"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Oh",
                        "sure",
                        ",",
                        "I",
                        "'d",
                        "be",
                        "happy",
                        "to",
                        "help",
                        "you",
                        "check",
                        "info",
                        ".",
                        "What",
                        "is",
                        "your",
                        "appt",
                        "date",
                        "?",
                        "last",
                        "Tuesday",
                    ],
                    "predicted_clusters": [[(9, 10), (15, 16)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (15, 16),
                        (15, 18),
                        (19, 21),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "July 1, 1980",
                            "normalizedValue": "1980-07-01T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.9754878282546997,
                            "token": "July 1, 1980",
                            "span": {"end": 12},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["july", "1", ",", "1980"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "OK.",
                        "What",
                        "is",
                        "your",
                        "birthday",
                        "?",
                        "July",
                        "1",
                        ",",
                        "1980",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (3, 4), (3, 5), (6, 10)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.9406614303588867,
                            "token": "Peter",
                            "span": {"end": 5},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["peter"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["OK.", "Can", "I", "get", "your", "name", "?", "Peter"],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3), (4, 5), (7, 8)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9737169742584229,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9737169742584229,
                        "sent": "No",
                    }
                ],
                "negation": {
                    "wordlist": ["none", "of", "them"],
                    "triplets": [(0, 3, 3)],
                },
                "coref": {
                    "words": [
                        "OK",
                        ".",
                        "I",
                        "got",
                        "multiple",
                        "possible",
                        "answers",
                        "for",
                        "new_appt_date",
                        ",",
                        "July",
                        "1",
                        ",",
                        "1980",
                        "and",
                        "November",
                        "2",
                        ",",
                        "2021",
                        ",",
                        "which",
                        "one",
                        "did",
                        "you",
                        "mean",
                        "?",
                        "None",
                        "of",
                        "them",
                    ],
                    "predicted_clusters": [[(2, 3), (23, 24)], [(8, 19), (28, 29)]],
                    "top_spans": [
                        (2, 3),
                        (3, 4),
                        (4, 19),
                        (8, 9),
                        (8, 14),
                        (8, 19),
                        (10, 12),
                        (10, 14),
                        (15, 19),
                        (23, 24),
                        (28, 29),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9737169742584229,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "next Tuesday",
                            "normalizedValue": "2021-11-09T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8437415361404419,
                            "token": "next Tuesday",
                            "span": {"end": 12},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["next", "tuesday"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Can",
                        "I",
                        "get",
                        "your",
                        "new",
                        "appt",
                        "date",
                        "?",
                        "next",
                        "Tuesday",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (3, 4), (3, 7), (8, 10)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]
        mocked_func.side_effect = [
            {"success": True, "msg": "Info collected: 2021-11-02"}
        ]
        user_inputs = [
            "check info",
            "last Tuesday",
            "July 1, 1980",
            "Peter",
            "None of them",
            "next Tuesday",
        ]
        target_responses = [
            ["your appt date?"],
            ["your birthday?"],
            ["your name?"],
            [
                "I got multiple possible answers for new_appt_date,",
                " July 1, 1980 and November 2, 2021, ",
                "which one did you mean?",
            ],
            ["your new appt date?"],
            [
                "OK. Your request has been completed.",
                "Is there anything else I can help you with today?",
            ],
        ]

        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

        # Only name is still in history, other three DATE entities were removed.
        self.assertNotEqual(ctx.entity_history_manager.history[4], set())  # name
        self.assertEqual(ctx.entity_history_manager.history[2], set())  # appt date
        self.assertEqual(ctx.entity_history_manager.history[3], set())  # birthday
        self.assertEqual(ctx.entity_history_manager.history[6], set())  # new appt date


if __name__ == "__main__":
    unittest.main()
