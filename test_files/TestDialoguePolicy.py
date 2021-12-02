# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
from unittest.mock import patch

from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.utils.utils import resp
import uuid
from Converse.dialog_context.dialog_context_manager import DialogContextManager


class TestDialoguePolicy(unittest.TestCase):
    """
    Dialogue Policy determines the next dialogue action based
    on current dialogue states.
    The output of policy tree execution is the response. We still
    use Orchestrator to test Dialogue Policy but with different
    policy configurations.
    """

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_no_confirm_abilities(self, mocked_info, mocked_func):
        """
        In this test case, we removed confirm entity and confirm task from
        policy config. Now the agent is not able to process confirmation info.
        """
        dm = Orchestrator(
            task_path="./test_files/test_task_config_shopping.yaml",
            entity_path="./test_files/test_entity_config_shopping.yaml",
            policy_path="./test_files/test_policy_config_1.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        dmgr.save(cid, ctx)

        user_inputs = [
            "I want to check order status",
            "peter@hotmail.com",
            "yes",
            "why are you asking me again?",
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
                "Okay, so P E T E R at hotmail dot com?",
            ],
            [
                "Okay, so P E T E R at hotmail dot com?",
            ],
            [
                "I am sorry, but I could not recognize your email_address.",
                "your zip code?",
            ],
            [
                (
                    "One moment please. Your order status is 10 pizza, placed but not"
                    " yet shipped. Please provide your order id for your order details."
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
                    "words": ["I", "want", "to", "check", "order", "status"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (4, 6)],
                },
                "final_intent": {
                    "intent": "check_order",
                    "prob": 0.9539812207221985,
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
                        "What",
                        "is",
                        "your",
                        "email",
                        "address",
                        "?",
                        "peter",
                        "@",
                        "hotmail.com",
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
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
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
                        "P",
                        "E",
                        "T",
                        "E",
                        "R",
                        "at",
                        "hotmail",
                        "dot",
                        "com",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(3, 13), (4, 5), (8, 9), (8, 13), (10, 11), (10, 13)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9752330780029297,
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
                    "wordlist": ["why", "are", "you", "asking", "me", "again", "?"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Okay",
                        ",",
                        "so",
                        "P",
                        "E",
                        "T",
                        "E",
                        "R",
                        "at",
                        "hotmail",
                        "dot",
                        "com",
                        "?",
                        "why",
                        "are",
                        "you",
                        "asking",
                        "me",
                        "again",
                        "?",
                    ],
                    "predicted_clusters": [[(8, 9), (16, 17)]],
                    "top_spans": [
                        (3, 13),
                        (8, 9),
                        (8, 13),
                        (10, 11),
                        (10, 13),
                        (16, 17),
                        (17, 18),
                        (18, 19),
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
                            "probability": 0.856576144695282,
                            "token": "94301",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.6365075707435608,
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

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_no_task_with_info(self, mocked_info, mock_func):
        """
        In this test case, we replace new_task_with_info with got_new_task in
        policy config. Now the agent is not able to process new task and info
        at the same time.
        """
        mock_func.return_value = resp(
            True,
            "Weather condition is {} at {}, {}".format(
                "few clouds", "Los Altos", 94022
            ),
        )

        mocked_info.side_effect = [
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.4922097623348236,
                            "token": "94022",
                            "normalizedValue": "AddressNumber:94022",
                            "span": {"start": 18, "end": 23},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9584088921546936,
                    "sent": "query the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9584088921546936,
                        "sent": "query the weather",
                    }
                ],
                "negation": {
                    "wordlist": ["check", "weather", "for", "94022"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["check", "weather", "for", "94022"],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4)],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9584088921546936,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7607815861701965,
                            "token": "94022",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9970296621322632,
                            "token": "94022",
                            "normalizedValue": "AddressNumber:94022",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["94022"], "triplets": [(-1, -1, -1)]},
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
                        "94022",
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
        ]

        user_inputs = ["check weather for 94022", "94022"]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you check local weather.",
                "your zip code?",
            ],
            [
                (
                    "Weather condition is few clouds at Los Altos, 94022. "
                    "Your request has been completed. "
                    "Is there anything else I can help you with today?"
                )
            ],
        ]

        dm = Orchestrator(
            task_path="./test_files/test_tasks.yaml",
            entity_path="./test_files/test_entity_config.yaml",
            policy_path="./test_files/test_policy_config_2.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_repeat_key_setting_refuse(self, mocked_info, mock_func):
        """
        In this test case, we test after the user refuse to repeat a task,
        whether the repeat key in DialogueContext is reset to False.
        """
        mock_func.side_effect = [
            resp(True, "{} inch equals to {} centimeter".format("3.0", "7.62")),
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "sent": "convert inch",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "convert_inch_to_cm",
                        "prob": 0.8471952676773071,
                        "sent": "convert inch",
                    }
                ],
                "negation": {
                    "wordlist": ["convert", "inch", "to", "centimeter"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["convert", "inch", "to", "centimeter"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7635552883148193,
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
                        "Can",
                        "I",
                        "get",
                        "your",
                        "inch",
                        "?",
                        "3",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)], [(9, 10), (18, 19)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (16, 17),
                        (17, 18),
                        (18, 19),
                        (18, 20),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9498212933540344,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9498212933540344,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["no", "thanks"], "triplets": [(0, 2, 2)]},
                "coref": {
                    "words": [
                        "3.0",
                        "inch",
                        "equals",
                        "to",
                        "7.62",
                        "centimeter",
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
                        "convert",
                        "inch",
                        "to",
                        "centimeter",
                        "again",
                        "?",
                        "no",
                        "thanks",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (0, 6),
                        (0, 9),
                        (4, 6),
                        (7, 8),
                        (7, 9),
                        (11, 12),
                        (14, 15),
                        (15, 16),
                        (17, 18),
                        (18, 21),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9498212933540344,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = ["convert inch to centimeter", "3", "no thanks"]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you convert inch to centimeter.",
                "your inch?",
            ],
            [
                (
                    "3.0 inch equals to 7.62 centimeter. "
                    "Your request has been completed. "
                    "Would you like to convert inch to centimeter again?"
                )
            ],
            ["Is there anything else I can help you with today?"],
        ]

        dm = Orchestrator(
            task_path="./test_files/test_repeat_task_config.yaml",
            entity_path="./test_files/test_repeat_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)
        self.assertEqual(ctx.repeat, False)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_repeat_key_setting_refuse_and_new_intent(self, mocked_info, mock_func):
        """
        In this test case, we test after the user refuse to repeat a task,
        and brings up a new intent,
        whether the repeat key in DialogueContext is reset to False.
        """
        mock_func.side_effect = [
            resp(True, "{} inch equals to {} centimeter".format("3.0", "7.62")),
        ]

        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "sent": "convert inch",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "convert_inch_to_cm",
                        "prob": 0.8471952676773071,
                        "sent": "convert inch",
                    }
                ],
                "negation": {
                    "wordlist": ["convert", "inch", "to", "centimeter"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["convert", "inch", "to", "centimeter"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7635552883148193,
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
                        "Can",
                        "I",
                        "get",
                        "your",
                        "inch",
                        "?",
                        "3",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)], [(9, 10), (18, 19)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (16, 17),
                        (17, 18),
                        (18, 19),
                        (18, 20),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_weather",
                    "prob": 0.9718443751335144,
                    "sent": "I want to check the weather",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_weather",
                        "prob": 0.9718443751335144,
                        "sent": "I want to check the weather",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "no",
                        ",",
                        "now",
                        "i",
                        "would",
                        "like",
                        "to",
                        "check",
                        "the",
                        "weather",
                    ],
                    "triplets": [(0, 2, 4)],
                },
                "coref": {
                    "words": [
                        "3.0",
                        "inch",
                        "equals",
                        "to",
                        "7.62",
                        "centimeter",
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
                        "convert",
                        "inch",
                        "to",
                        "centimeter",
                        "again",
                        "?",
                        "no",
                        ",",
                        "now",
                        "I",
                        "would",
                        "like",
                        "to",
                        "check",
                        "the",
                        "weather",
                    ],
                    "predicted_clusters": [[(14, 15), (26, 27)]],
                    "top_spans": [
                        (0, 6),
                        (0, 9),
                        (4, 6),
                        (7, 8),
                        (7, 9),
                        (11, 12),
                        (14, 15),
                        (15, 16),
                        (17, 18),
                        (18, 21),
                        (26, 27),
                        (30, 31),
                        (31, 33),
                    ],
                },
                "final_intent": {
                    "intent": "check_weather",
                    "prob": 0.9718443751335144,
                    "uncertain": True,
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
                        "So",
                        "you",
                        "want",
                        "to",
                        "check",
                        "local",
                        "weather",
                        ",",
                        "right",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (2, 3), (4, 5), (5, 7)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.9713575839996338,
                    "uncertain": False,
                },
            },
        ]

        user_inputs = [
            "convert inch to centimeter",
            "3",
            "no, now I would like to check the weather",
            "yes",
        ]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you convert inch to centimeter.",
                "your inch?",
            ],
            [
                (
                    "3.0 inch equals to 7.62 centimeter. "
                    "Your request has been completed. "
                    "Would you like to convert inch to centimeter again?"
                )
            ],
            ["So you want to check local weather, right?"],
            [
                "Oh sure, I'd be happy to help you check local weather.",
                "your zip code?",
            ],
        ]

        dm = Orchestrator(
            task_path="./test_files/test_repeat_task_config.yaml",
            entity_path="./test_files/test_repeat_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)
        self.assertEqual(ctx.repeat, False)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_repeat_key_setting_repeat(self, mocked_info, mock_func):
        """
        In this test case, we test after the user confirm to repeat a task,
        whether the repeat key in DialogueContext is set to True.
        """
        mock_func.side_effect = [
            resp(True, "{} inch equals to {} centimeter".format("3.0", "7.62")),
            resp(True, "{} inch equals to {} centimeter".format("4.0", "10.16")),
        ]
        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "sent": "convert inch",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "convert_inch_to_cm",
                        "prob": 0.8471952676773071,
                        "sent": "convert inch",
                    }
                ],
                "negation": {
                    "wordlist": ["convert", "inch", "to", "centimeter"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["convert", "inch", "to", "centimeter"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1)],
                },
                "final_intent": {
                    "intent": "convert_inch_to_cm",
                    "prob": 0.8471952676773071,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.7635552883148193,
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
                        "Can",
                        "I",
                        "get",
                        "your",
                        "inch",
                        "?",
                        "3",
                    ],
                    "predicted_clusters": [[(3, 4), (16, 17)], [(9, 10), (18, 19)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (16, 17),
                        (17, 18),
                        (18, 19),
                        (18, 20),
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
                            "probability": 0.7843295335769653,
                            "token": "4",
                            "span": {"start": 11, "end": 12},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8773074746131897,
                    "sent": "Yes",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8773074746131897,
                        "sent": "Yes",
                    }
                ],
                "negation": {
                    "wordlist": ["yes", "please", "4"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "3.0",
                        "inch",
                        "equals",
                        "to",
                        "7.62",
                        "centimeter",
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
                        "convert",
                        "inch",
                        "to",
                        "centimeter",
                        "again",
                        "?",
                        "yes",
                        "please",
                        "4",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (0, 6),
                        (0, 9),
                        (4, 6),
                        (7, 8),
                        (7, 9),
                        (11, 12),
                        (14, 15),
                        (15, 16),
                        (17, 18),
                        (18, 21),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8773074746131897,
                    "uncertain": False,
                },
            },
        ]
        dm = Orchestrator(
            task_path="./test_files/test_repeat_task_config.yaml",
            entity_path="./test_files/test_repeat_entity_config.yaml",
        )
        dmgr = DialogContextManager.new_instance("memory")
        cid = str(uuid.uuid4())
        ctx = dmgr.reset_ctx(
            cid,
            dm.policy_layer.state_manager.entity_manager.entity_config,
            dm.policy_layer.state_manager.task_config,
            dm.policy_layer.bot_config,
        )
        user_inputs = ["convert inch to centimeter", "3", "yes please 4 inch"]

        target_responses = [
            [
                "Oh sure, I'd be happy to help you convert inch to centimeter.",
                "your inch?",
            ],
            [
                (
                    "3.0 inch equals to 7.62 centimeter. "
                    "Your request has been completed. "
                    "Would you like to convert inch to centimeter again?"
                )
            ],
            [
                (
                    "4.0 inch equals to 10.16 centimeter. "
                    "Your request has been completed. "
                    "Would you like to convert inch to centimeter again?"
                )
            ],
        ]
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)
        self.assertEqual(ctx.repeat, True)

    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_continuous_no_info_turn(self, mocked_info):
        """
        In this test case, we test after the continuous_no_info_turn
        exceeds the max_no_info_turn, whether the system will say goodbye.
        """
        mocked_info.side_effect = [
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": ["something"],
                    "predicted_clusters": [],
                    "top_spans": [],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
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
                        "check",
                        "your",
                        "order",
                        "status",
                        "2.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "3.",
                        "pull",
                        "up",
                        "your",
                        "account",
                        "You",
                        "can",
                        "try",
                        "to",
                        "say",
                        "something",
                        "about",
                        "these",
                        "tasks",
                        ".",
                        "something",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (21, 22), (28, 29), (33, 34), (35, 36)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (28, 29),
                        (28, 30),
                        (31, 32),
                        (33, 34),
                        (33, 35),
                        (35, 36),
                        (37, 38),
                        (39, 40),
                        (42, 44),
                        (45, 46),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
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
                        "check",
                        "your",
                        "order",
                        "status",
                        "2.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "3.",
                        "pull",
                        "up",
                        "your",
                        "account",
                        "You",
                        "can",
                        "try",
                        "to",
                        "say",
                        "something",
                        "about",
                        "these",
                        "tasks",
                        ".",
                        "something",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (21, 22), (28, 29), (33, 34), (35, 36)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (28, 29),
                        (28, 30),
                        (31, 32),
                        (33, 34),
                        (33, 35),
                        (35, 36),
                        (37, 38),
                        (39, 40),
                        (42, 44),
                        (45, 46),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
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
                        "check",
                        "your",
                        "order",
                        "status",
                        "2.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "3.",
                        "pull",
                        "up",
                        "your",
                        "account",
                        "You",
                        "can",
                        "try",
                        "to",
                        "say",
                        "something",
                        "about",
                        "these",
                        "tasks",
                        ".",
                        "something",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (21, 22), (28, 29), (33, 34), (35, 36)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (28, 29),
                        (28, 30),
                        (31, 32),
                        (33, 34),
                        (33, 35),
                        (35, 36),
                        (37, 38),
                        (39, 40),
                        (42, 44),
                        (45, 46),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
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
                        "check",
                        "your",
                        "order",
                        "status",
                        "2.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "3.",
                        "pull",
                        "up",
                        "your",
                        "account",
                        "You",
                        "can",
                        "try",
                        "to",
                        "say",
                        "something",
                        "about",
                        "these",
                        "tasks",
                        ".",
                        "something",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (21, 22), (28, 29), (33, 34), (35, 36)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (28, 29),
                        (28, 30),
                        (31, 32),
                        (33, 34),
                        (33, 35),
                        (35, 36),
                        (37, 38),
                        (39, 40),
                        (42, 44),
                        (45, 46),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["something"], "triplets": [(-1, -1, -1)]},
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
                        "check",
                        "your",
                        "order",
                        "status",
                        "2.",
                        "add",
                        "more",
                        "to",
                        "your",
                        "order",
                        "3.",
                        "pull",
                        "up",
                        "your",
                        "account",
                        "You",
                        "can",
                        "try",
                        "to",
                        "say",
                        "something",
                        "about",
                        "these",
                        "tasks",
                        ".",
                        "something",
                    ],
                    "predicted_clusters": [
                        [(0, 1), (4, 5), (15, 16)],
                        [(9, 10), (21, 22), (28, 29), (33, 34), (35, 36)],
                    ],
                    "top_spans": [
                        (0, 1),
                        (4, 5),
                        (9, 10),
                        (15, 16),
                        (20, 21),
                        (21, 22),
                        (21, 24),
                        (25, 26),
                        (28, 29),
                        (28, 30),
                        (31, 32),
                        (33, 34),
                        (33, 35),
                        (35, 36),
                        (37, 38),
                        (39, 40),
                        (42, 44),
                        (45, 46),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]
        dm = Orchestrator(
            task_path="./test_files/test_repeat_task_config.yaml",
            entity_path="./test_files/test_repeat_entity_config.yaml",
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
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
        ]

        target_responses = [
            "I am sorry that I couldn't understand what you said.",
            "I am sorry that I couldn't understand what you said.",
            "I am sorry that I couldn't understand what you said.",
            "I am sorry that I couldn't understand what you said.",
            "I am sorry that I couldn't understand what you said.",
            "Let me forward this case to one of our professional agents. Please wait for 5 minutes.",
        ]

        continuous_no_info_flags = [0, 1, 2, 3, 4, 5]
        prev_no_info_flags = [False, True, True, True, True, True]

        for user_input, target, c_flag, p_flag in zip(
            user_inputs, target_responses, continuous_no_info_flags, prev_no_info_flags
        ):
            self.assertEqual(ctx.cur_states.continuous_no_info_turn, c_flag)
            self.assertEqual(ctx.cur_states.prev_turn_no_info, p_flag)
            res = dm.process(user_input, user_input, ctx)
            dmgr.save(cid, ctx)
            for tgt in target:
                self.assertIn(tgt, res)
