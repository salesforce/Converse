# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
from unittest.mock import patch
import uuid

from Converse.dialog_context.dialog_context_manager import DialogContextManager
from Converse.dialog_orchestrator.orchestrator import Orchestrator


class TestTemplateBots(unittest.TestCase):
    """
    Unit tests for template bots.
    """

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_online_shopping(self, mocked_info, mocked_func):
        """
        Unit test for online shopping example.
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/online_shopping/tasks.yaml",
            entity_path="./Converse/bot_configs/online_shopping/entity_config.yaml",
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
            "correct",
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
        ]
        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_health_appointment(self, mocked_info, mocked_func):
        """
        Unit test for health appointment template bot
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/health_appointment/tasks.yaml",
            entity_path="./Converse/bot_configs/health_appointment/entity_config.yaml",
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
                            "token": "tomorrow",
                            "normalizedValue": "2021-10-16T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8234410285949707,
                            "token": "tomorrow",
                            "span": {"end": 8},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["tomorrow"], "triplets": [(-1, -1, -1)]},
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
                        "date",
                        "do",
                        "you",
                        "prefer",
                        "for",
                        "the",
                        "appointment",
                        "?",
                        "tomorrow",
                    ],
                    "predicted_clusters": [[(9, 10), (20, 21)], [(11, 17), (24, 26)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 17),
                        (11, 26),
                        (14, 17),
                        (20, 21),
                        (20, 26),
                        (24, 26),
                        (27, 28),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "TIME",
                            "probability": 0.8673790097236633,
                            "token": "10am",
                            "span": {"start": 3, "end": 7},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["at", "10am"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "At",
                        "what",
                        "time",
                        "?",
                        "At",
                        "10am",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (1, 2), (8, 9)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["general", "surgery"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Okay",
                        ".",
                        "Which",
                        "department",
                        "do",
                        "you",
                        "want",
                        "to",
                        "make",
                        "the",
                        "appointment",
                        "with",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "ICU",
                        "-",
                        "Elderly",
                        "services",
                        "-",
                        "Diagnostic",
                        "Imaging",
                        "-",
                        "General",
                        "Surgery",
                        "-",
                        "Neurology",
                        "-",
                        "Microbiology",
                        "-",
                        "Nutrition",
                        "and",
                        "Dietetics",
                        "General",
                        "surgery",
                    ],
                    "predicted_clusters": [[(5, 6), (13, 14)]],
                    "top_spans": [
                        (5, 6),
                        (6, 7),
                        (8, 9),
                        (9, 11),
                        (9, 12),
                        (9, 15),
                        (13, 14),
                        (13, 15),
                        (15, 16),
                        (16, 17),
                        (16, 18),
                        (20, 23),
                        (20, 29),
                        (20, 36),
                        (20, 38),
                        (38, 40),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.8770175576210022,
                            "token": "Harry",
                            "span": {"end": 5},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["harry"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Can",
                        "I",
                        "get",
                        "your",
                        "doctor",
                        "name",
                        "?",
                        "Harry",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (4, 5), (6, 7), (10, 11)],
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
                        "Got",
                        "it",
                        ".",
                        "Do",
                        "you",
                        "have",
                        "health",
                        "insurance",
                        "?",
                        "yes",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (4, 5), (5, 6), (6, 8)],
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
                            "probability": 0.6666074395179749,
                            "token": "1234",
                            "span": {"end": 4},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9788269996643066,
                            "token": "1234",
                            "normalizedValue": "AddressNumber:1234",
                            "span": {"end": 4},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["1234"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "OK.",
                        "May",
                        "I",
                        "have",
                        "the",
                        "last",
                        "four",
                        "digits",
                        "of",
                        "your",
                        "social",
                        "security",
                        "number",
                        "?",
                        "1234",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(1, 2), (2, 3), (3, 4), (4, 13), (9, 10), (9, 13)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "March 14, 1994",
                            "normalizedValue": "1994-03-14T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.9664927124977112,
                            "token": "March 14, 1994",
                            "span": {"start": 19, "end": 33},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.6755425930023193,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9781754016876221,
                        "sent": "No",
                    },
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                ],
                "negation": {
                    "wordlist": [
                        "no",
                        ".",
                        "my",
                        "birthday",
                        "is",
                        "march",
                        "14",
                        ",",
                        "1994",
                    ],
                    "triplets": [(0, 3, 6)],
                },
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Your",
                        "birthday",
                        "is",
                        "October",
                        "17",
                        ",",
                        "2021",
                        ".",
                        "Is",
                        "that",
                        "correct",
                        "?",
                        "no",
                        ".",
                        "my",
                        "birthday",
                        "is",
                        "March",
                        "14",
                        ",",
                        "1994",
                    ],
                    "predicted_clusters": [[(3, 4), (17, 18)], [(3, 5), (17, 19)]],
                    "top_spans": [
                        (1, 2),
                        (3, 4),
                        (3, 5),
                        (6, 10),
                        (6, 13),
                        (12, 13),
                        (17, 18),
                        (17, 19),
                        (20, 24),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
        ]

        mocked_func.side_effect = [
            {"success": True, "msg": "Info collected: 2021-10-16"},
            {"success": True, "msg": "Info collected: 10am"},
            {"success": True, "msg": "Info collected: General Surgery"},
            {"success": True, "msg": "Info collected: Harry"},
            {"success": True, "msg": "OK."},
            {"success": True, "msg": "OK"},
            {"success": True, "msg": "OK"},
        ]

        user_inputs = [
            "I want to see a doctor",
            "tomorrow",
            "At 10am",
            "General surgery",
            "Harry",
            "yes",
            "1234",
            "no. my birthday is March 14, 1994",
        ]
        target_responses = [
            [
                "make an appointment at Nurse Nancy.",
                "What date do you prefer for the appointment?",
            ],
            ["At what time?"],
            [
                "Which department do you want to make the appointment with?\n",
                "Your choices are listed here:\n",
                "- ICU\n",
                "- Elderly services\n",
                "- Diagnostic Imaging\n",
                "- General Surgery\n",
                "- Neurology\n",
                "- Microbiology\n",
                "- Nutrition and Dietetics",
            ],
            ["your preferred doctor name?"],
            ["Do you have health insurance?"],
            ["May I have the last four digits of your social security number?"],
            ["Your birthday is October 16, 2021.", "Is that correct?"],
            [
                "I have found your health insurance record.",
                "If you have COVID-19 symptoms,",
                "immediately self-isolate and contact your local public health authority",
                "or healthcare provider.",
                "Wear a mask, stay at least 6 feet from others,",
                "wash your hands, avoid crowds, and take other steps",
                "to prevent the spread of COVID-19. I have booked an appointment for you.",
            ],
        ]
        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)
            self.assertNotIn("I have created a profile for you.", res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_book_movie_tickets(self, mocked_info, mocked_func):
        """
        Unit test for book movie tickets template bot
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/book_movie_tickets/tasks.yaml",
            entity_path="./Converse/bot_configs/book_movie_tickets/entity_config.yaml",
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
                    "intent": "movies_in_theater",
                    "prob": 0.96988844871521,
                    "sent": "what movies are being shown today ?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "movies_in_theater",
                        "prob": 0.96988844871521,
                        "sent": "what movies are being shown today ?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "hi",
                        ",",
                        "what",
                        "movies",
                        "are",
                        "in",
                        "theater",
                        "now",
                        "?",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        ",",
                        "what",
                        "movies",
                        "are",
                        "in",
                        "theater",
                        "now",
                        "?",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(3, 4), (4, 5), (6, 7)],
                },
                "final_intent": {
                    "intent": "movies_in_theater",
                    "prob": 0.96988844871521,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "book_movie_tickets",
                    "prob": 0.9616244435310364,
                    "sent": "Can I buy tickets for a movie",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "book_movie_tickets",
                        "prob": 0.9616244435310364,
                        "sent": "Can I buy tickets for a movie",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "to", "buy", "movie", "tickets"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Here",
                        "are",
                        "the",
                        "movies",
                        "in",
                        "theater",
                        "now",
                        ":",
                        "-",
                        "The",
                        "Shawshank",
                        "Redemption",
                        "(",
                        "1994",
                        ")",
                        "-",
                        "The",
                        "Godfather",
                        "(",
                        "1972",
                        ")",
                        "-",
                        "'The",
                        "Godfather",
                        ":",
                        "Part",
                        "II",
                        "(",
                        "1974",
                        ")",
                        "'",
                        "-",
                        "The",
                        "Dark",
                        "Knight",
                        "(",
                        "2008",
                        ")",
                        "-",
                        "12",
                        "Angry",
                        "Men",
                        "(",
                        "1957",
                        ")",
                        "-",
                        "Schindler",
                        "'s",
                        "List",
                        "(",
                        "1993",
                        ")",
                        "-",
                        "'The",
                        "Lord",
                        "of",
                        "the",
                        "Rings",
                        ":",
                        "The",
                        "Return",
                        "of",
                        "the",
                        "King",
                        "(",
                        "2003",
                        ")",
                        "'",
                        "-",
                        "Pulp",
                        "Fiction",
                        "(",
                        "1994",
                        ")",
                        "-",
                        "The",
                        "Good",
                        ",",
                        "the",
                        "Bad",
                        "and",
                        "the",
                        "Ugly",
                        "(",
                        "1966",
                        ")",
                        "-",
                        "'The",
                        "Lord",
                        "of",
                        "the",
                        "Rings",
                        ":",
                        "The",
                        "Fellowship",
                        "of",
                        "the",
                        "Ring",
                        "(",
                        "2001",
                        ")",
                        "'",
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
                        "I",
                        "want",
                        "to",
                        "buy",
                        "movie",
                        "tickets",
                    ],
                    "predicted_clusters": [[(102, 103), (115, 116), (119, 120)]],
                    "top_spans": [
                        (5, 6),
                        (13, 14),
                        (13, 20),
                        (13, 23),
                        (13, 24),
                        (16, 18),
                        (16, 20),
                        (19, 20),
                        (25, 27),
                        (25, 29),
                        (25, 30),
                        (25, 37),
                        (25, 42),
                        (32, 35),
                        (32, 37),
                        (36, 37),
                        (43, 44),
                        (43, 51),
                        (50, 51),
                        (59, 71),
                        (59, 73),
                        (62, 64),
                        (62, 67),
                        (62, 71),
                        (65, 66),
                        (65, 67),
                        (72, 73),
                        (75, 80),
                        (75, 83),
                        (75, 92),
                        (84, 85),
                        (84, 92),
                        (93, 100),
                        (93, 101),
                        (93, 104),
                        (96, 98),
                        (96, 100),
                        (99, 100),
                        (102, 103),
                        (102, 104),
                        (106, 107),
                        (110, 118),
                        (112, 113),
                        (114, 115),
                        (115, 116),
                        (117, 118),
                        (119, 120),
                        (120, 121),
                        (122, 123),
                        (123, 125),
                    ],
                },
                "final_intent": {
                    "intent": "book_movie_tickets",
                    "prob": 0.9616244435310364,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.7015067338943481,
                            "token": "The Godfather,",
                            "span": {"end": 14},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.8206571340560913,
                    "sent": "yes please",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.8206571340560913,
                        "sent": "yes please",
                    }
                ],
                "negation": {
                    "wordlist": ["the", "godfather", ",", "please"],
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
                        "movie",
                        "tickets",
                        "at",
                        "Old",
                        "Movie",
                        "Theater",
                        ".",
                        "Which",
                        "movie",
                        "do",
                        "you",
                        "want",
                        "to",
                        "see",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "The",
                        "Shawshank",
                        "Redemption",
                        "(",
                        "1994",
                        ")",
                        "-",
                        "The",
                        "Godfather",
                        "(",
                        "1972",
                        ")",
                        "-",
                        "The",
                        "Godfather",
                        ":",
                        "Part",
                        "II",
                        "(",
                        "1974",
                        ")",
                        "-",
                        "The",
                        "Dark",
                        "Knight",
                        "(",
                        "2008",
                        ")",
                        "-",
                        "12",
                        "Angry",
                        "Men",
                        "(",
                        "1957",
                        ")",
                        "-",
                        "Schindler",
                        "'s",
                        "List",
                        "(",
                        "1993",
                        ")",
                        "-",
                        "The",
                        "Lord",
                        "of",
                        "the",
                        "Rings",
                        ":",
                        "The",
                        "Return",
                        "of",
                        "the",
                        "King",
                        "(",
                        "2003",
                        ")",
                        "-",
                        "Pulp",
                        "Fiction",
                        "(",
                        "1994",
                        ")",
                        "-",
                        "The",
                        "Good",
                        ",",
                        "the",
                        "Bad",
                        "and",
                        "the",
                        "Ugly",
                        "(",
                        "1966",
                        ")",
                        "-",
                        "The",
                        "Lord",
                        "of",
                        "the",
                        "Rings",
                        ":",
                        "The",
                        "Fellowship",
                        "of",
                        "the",
                        "Ring",
                        "(",
                        "2001",
                        ")",
                        "The",
                        "Godfather",
                        ",",
                        "please",
                    ],
                    "predicted_clusters": [[(9, 10), (21, 22), (26, 27)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 17),
                        (11, 20),
                        (14, 17),
                        (21, 22),
                        (26, 27),
                        (26, 28),
                        (29, 30),
                        (33, 51),
                        (37, 38),
                        (37, 42),
                        (37, 48),
                        (37, 51),
                        (40, 42),
                        (43, 44),
                        (43, 48),
                        (46, 48),
                        (49, 51),
                        (52, 53),
                        (52, 58),
                        (55, 58),
                        (59, 60),
                        (59, 65),
                        (59, 74),
                        (66, 67),
                        (66, 74),
                        (73, 74),
                        (76, 81),
                        (76, 87),
                        (76, 89),
                        (76, 93),
                        (76, 95),
                        (85, 87),
                        (88, 89),
                        (94, 95),
                        (97, 102),
                        (97, 105),
                        (97, 107),
                        (97, 114),
                        (97, 122),
                        (109, 114),
                        (115, 122),
                        (118, 122),
                        (121, 122),
                        (123, 125),
                        (123, 127),
                    ],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.8206571340560913,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "Tomorrow",
                            "normalizedValue": "2021-10-16T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8234410285949707,
                            "token": "Tomorrow",
                            "span": {"end": 8},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["tomorrow"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Great",
                        "choice",
                        "!",
                        "What",
                        "date",
                        "do",
                        "you",
                        "prefer",
                        "?",
                        "Tomorrow",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(0, 2), (4, 5), (6, 7), (9, 10)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "3pm",
                            "normalizedValue": "2021-10-16T15:00:00.000Z",
                        },
                        {
                            "label": "TIME",
                            "probability": 0.9315290451049805,
                            "token": "3pm",
                            "span": {"end": 3},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.7649067640304565,
                            "token": "3pm",
                            "normalizedValue": "AddressNumber:3pm",
                            "span": {"end": 3},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["3pm"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "And",
                        "what",
                        "time",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "10:00",
                        "AM",
                        "-",
                        "12:30",
                        "PM",
                        "-",
                        "3:00",
                        "PM",
                        "-",
                        "5:30",
                        "PM",
                        "-",
                        "8:00",
                        "PM",
                        "3pm",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (1, 2),
                        (1, 6),
                        (7, 8),
                        (7, 9),
                        (9, 10),
                        (10, 11),
                        (10, 12),
                        (14, 28),
                        (15, 18),
                        (15, 28),
                        (28, 29),
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
                            "probability": 0.8135352730751038,
                            "token": "2",
                            "span": {"end": 1},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["2", "tickets"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "How",
                        "many",
                        "tickets",
                        "do",
                        "you",
                        "want",
                        "to",
                        "buy",
                        "?",
                        "2",
                        "tickets",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(2, 10), (3, 5), (3, 10), (6, 7), (11, 13)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "parking",
                    "prob": 0.9214711785316467,
                    "sent": "How do I park my car ?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "parking",
                        "prob": 0.9214711785316467,
                        "sent": "How do I park my car ?",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "oh",
                        ",",
                        "i",
                        "want",
                        "to",
                        "know",
                        "how",
                        "to",
                        "park",
                        "my",
                        "car",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "All",
                        "set",
                        ".",
                        "I",
                        "booked",
                        "your",
                        "tickets",
                        ".",
                        "I",
                        "look",
                        "forward",
                        "to",
                        "seeing",
                        "you",
                        "at",
                        "Old",
                        "Movie",
                        "Theater",
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
                        "Oh",
                        ",",
                        "I",
                        "want",
                        "to",
                        "know",
                        "how",
                        "to",
                        "park",
                        "my",
                        "car",
                    ],
                    "predicted_clusters": [
                        [(3, 4), (10, 11), (25, 26)],
                        [(7, 8), (15, 16), (28, 29), (34, 35), (41, 42)],
                    ],
                    "top_spans": [
                        (0, 2),
                        (3, 4),
                        (6, 7),
                        (7, 8),
                        (7, 9),
                        (10, 11),
                        (14, 15),
                        (15, 16),
                        (17, 20),
                        (23, 31),
                        (25, 26),
                        (28, 29),
                        (30, 31),
                        (34, 35),
                        (40, 41),
                        (41, 42),
                        (41, 43),
                    ],
                },
                "final_intent": {
                    "intent": "parking",
                    "prob": 0.9214711785316467,
                    "uncertain": False,
                },
            },
        ]
        message_1 = """Here are the movies in theater now:
      - The Shawshank Redemption (1994)
      - The Godfather (1972)
      - 'The Godfather: Part II (1974)'
      - The Dark Knight (2008)
      - 12 Angry Men (1957)
      - Schindler's List (1993)
      - 'The Lord of the Rings: The Return of the King (2003)'
      - Pulp Fiction (1994)
      - The Good, the Bad and the Ugly (1966)
      - 'The Lord of the Rings: The Fellowship of the Ring (2001)'
    """
        mocked_func.side_effect = [
            {"success": True, "msg": message_1},
            {"success": True, "msg": "Info collected: The Godfather (1972)"},
            {"success": True, "msg": "Info collected: 2021-10-16"},
            {"success": True, "msg": "Info collected: 3:00 PM"},
            {"success": True, "msg": "Info collected: 2"},
        ]

        user_inputs = [
            "Hi, what movies are in theater now?",
            "I want to buy movie tickets",
            "The Godfather, please",
            "Tomorrow",
            "3pm",
            "2 tickets",
            "Oh, I want to know how to park my car",
        ]
        target_responses = [
            [
                "Here are the movies in theater now:\n",
                "- The Shawshank Redemption (1994)\n",
                "- The Godfather (1972)\n",
                "- The Godfather: Part II (1974)\n",
                "- The Dark Knight (2008)\n",
                "- 12 Angry Men (1957)\n",
                "- Schindler's List (1993)\n",
                "- The Lord of the Rings: The Return of the King (2003)\n",
                "- Pulp Fiction (1994)\n",
                "- The Good, the Bad and the Ugly (1966)\n",
                "- The Lord of the Rings: The Fellowship of the Ring (2001)\n",
                "Your request has been completed. Is there anything else I can help you with today?",
            ],
            [
                "book movie tickets at Old Movie Theater. Which movie do you want to see?",
                "Your choices are listed here:\n",
                "- The Shawshank Redemption (1994)\n",
                "- The Godfather (1972)\n",
                "- The Godfather: Part II (1974)\n",
                "- The Dark Knight (2008)\n",
                "- 12 Angry Men (1957)\n",
                "- Schindler's List (1993)\n",
                "- The Lord of the Rings: The Return of the King (2003)\n",
                "- Pulp Fiction (1994)\n",
                "- The Good, the Bad and the Ugly (1966)\n",
                "- The Lord of the Rings: The Fellowship of the Ring (2001)",
            ],
            ["Great choice!", "What date do you prefer?"],
            [
                "Got it. And what time?\n",
                "Your choices are listed here:\n",
                "- 10:00 AM\n",
                "- 12:30 PM\n",
                "- 3:00 PM\n",
                "- 5:30 PM\n",
                "- 8:00 PM",
            ],
            ["Got it. How many tickets do you want to buy?"],
            [
                "All set.",
                "I booked your tickets. I look forward to seeing you at Old Movie Theater.",
            ],
            [
                "Convenient, free guest parking is located next to the theater.",
                "The entrance to the 7-story parking garage is off California Street, past the front of the theater.",
            ],
        ]
        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_banking(self, mocked_info, mocked_func):
        """
        Unit test for banking template bot
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/banking/tasks.yaml",
            entity_path="./Converse/bot_configs/banking/entity_config.yaml",
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
                    "intent": "credit_card_not_working",
                    "prob": 0.9841602444648743,
                    "sent": "my credit card is not working",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "credit_card_not_working",
                        "prob": 0.9841602444648743,
                        "sent": "my credit card is not working",
                    }
                ],
                "negation": {
                    "wordlist": ["my", "credit", "card", "is", "not", "working"],
                    "triplets": [(4, 5, 6)],
                },
                "coref": {
                    "words": ["my", "credit", "card", "is", "not", "working"],
                    "predicted_clusters": [],
                    "top_spans": [(0, 1), (0, 3)],
                },
                "final_intent": {
                    "intent": "credit_card_not_working",
                    "prob": 0.9841602444648743,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.8702093362808228,
                            "token": "Peter Parker",
                            "span": {"start": 11, "end": 23},
                        }
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["my", "name", "is", "peter", "parker"],
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
                        "resolve",
                        "your",
                        "credit",
                        "card",
                        "issues",
                        ".",
                        "First",
                        ",",
                        "I",
                        "need",
                        "to",
                        "verify",
                        "your",
                        "identity",
                        ".",
                        "What",
                        "'s",
                        "your",
                        "name",
                        "?",
                        "My",
                        "name",
                        "is",
                        "Peter",
                        "Parker",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (22, 23), (27, 28), (30, 31), (33, 35)],
                        [(3, 4), (18, 19)],
                        [(27, 29), (30, 32)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 15),
                        (18, 19),
                        (21, 22),
                        (22, 23),
                        (22, 24),
                        (27, 28),
                        (27, 29),
                        (30, 31),
                        (30, 32),
                        (33, 35),
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
                            "probability": 0.40036481618881226,
                            "token": "4000000000000000",
                            "span": {"start": 6, "end": 22},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.8280308842658997,
                            "token": "4000000000000000",
                            "normalizedValue": "ZipCode:4000000000000000",
                            "span": {"start": 6, "end": 22},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["it", "is", "4000000000000000"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Hi",
                        ",",
                        "Peter",
                        ".",
                        "May",
                        "I",
                        "have",
                        "your",
                        "credit",
                        "card",
                        "number",
                        "?",
                        "it",
                        "is",
                        "4000000000000000",
                    ],
                    "predicted_clusters": [[(2, 3), (7, 8)], [(7, 11), (12, 13)]],
                    "top_spans": [(2, 3), (5, 6), (6, 7), (7, 8), (7, 11), (12, 13)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.5419649481773376,
                            "token": "95100",
                            "span": {"end": 5},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.7714598178863525,
                            "token": "95100",
                            "normalizedValue": "ZipCode:95100",
                            "span": {"end": 5},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["95100"], "triplets": [(-1, -1, -1)]},
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "Could",
                        "you",
                        "please",
                        "confirm",
                        "the",
                        "zip",
                        "code",
                        "of",
                        "your",
                        "primary",
                        "address",
                        "?",
                        "95100",
                    ],
                    "predicted_clusters": [[(4, 5), (11, 12)]],
                    "top_spans": [
                        (1, 2),
                        (4, 5),
                        (7, 14),
                        (11, 12),
                        (11, 14),
                        (15, 16),
                    ],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "check_balance",
                    "prob": 0.9757109880447388,
                    "sent": "how much do I need to pay?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "check_balance",
                        "prob": 0.9757109880447388,
                        "sent": "how much do I need to pay?",
                    }
                ],
                "negation": {
                    "wordlist": ["how", "much", "do", "i", "need", "to", "pay", "?"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Okay",
                        ".",
                        "Perfect",
                        ".",
                        "I",
                        "pulled",
                        "up",
                        "your",
                        "account",
                        ".",
                        "It",
                        "seems",
                        "that",
                        "your",
                        "credit",
                        "card",
                        "has",
                        "been",
                        "suspended",
                        "because",
                        "you",
                        "balance",
                        "has",
                        "not",
                        "been",
                        "paid",
                        "for",
                        "3",
                        "months",
                        ".",
                        "We",
                        "will",
                        "re-activate",
                        "your",
                        "credit",
                        "card",
                        "as",
                        "soon",
                        "as",
                        "we",
                        "receive",
                        "the",
                        "payment",
                        "in",
                        "full",
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
                        "how",
                        "much",
                        "do",
                        "I",
                        "need",
                        "to",
                        "pay",
                        "?",
                    ],
                    "predicted_clusters": [
                        [
                            (7, 8),
                            (13, 14),
                            (20, 21),
                            (33, 34),
                            (46, 47),
                            (59, 60),
                            (66, 67),
                        ],
                        [(13, 16), (33, 36)],
                        [(30, 31), (39, 40)],
                        [(4, 5), (56, 57)],
                    ],
                    "top_spans": [
                        (4, 5),
                        (5, 6),
                        (6, 7),
                        (7, 8),
                        (7, 9),
                        (13, 14),
                        (13, 16),
                        (18, 19),
                        (20, 21),
                        (20, 22),
                        (25, 26),
                        (27, 29),
                        (30, 31),
                        (32, 33),
                        (33, 34),
                        (33, 36),
                        (39, 40),
                        (40, 41),
                        (41, 43),
                        (46, 47),
                        (46, 48),
                        (50, 51),
                        (54, 62),
                        (56, 57),
                        (59, 60),
                        (61, 62),
                        (66, 67),
                        (67, 68),
                    ],
                },
                "final_intent": {
                    "intent": "check_balance",
                    "prob": 0.9757109880447388,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            {"success": True, "msg": "Hi, Peter"},
            {"success": True, "msg": "Card number verified"},
            {"success": True, "msg": "Zip code verified"},
            {
                "success": True,
                "msg": "It seems that your credit card has been suspended"
                " because your balance has not been paid for 3 months."
                " We will re-activate your credit card as soon as we "
                "receive the payment in full.",
            },
            {"success": True, "msg": "Your balance due is $250.13."},
        ]

        user_inputs = [
            "my credit card is not working",
            "My name is Peter Parker",
            "it is 4000000000000000",
            "95100",
            "how much do I need to pay?",
        ]
        target_responses = [
            [
                "resolve your credit card issues.",
                "First, I need to verify your identity.",
                "What's your name?",
            ],
            ["Hi, Peter. May I have your credit card number?"],
            ["Could you please confirm the zip code of your primary address?"],
            [
                "Perfect. I pulled up your account.",
                (
                    "It seems that your credit card has been suspended"
                    " because your balance has not been paid for 3 months. "
                ),
                (
                    "We will re-activate your credit card as "
                    "soon as we receive the payment in full."
                ),
            ],
            [
                "Your balance due is $250.13.",
                "Your request has been completed.",
                "Is there anything else I can help you with today?",
            ],
        ]

        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

    @patch("Converse.dialog_state_manager.dial_state_manager.entity_api_call")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_manufactory(self, mocked_info, mocked_func):
        """
        Unit test for manufacturing template bot
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/manufacturing/tasks.yaml",
            entity_path="./Converse/bot_configs/manufacturing/entity_config.yaml",
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
                    "intent": "customize_tshirt",
                    "prob": 0.9762795567512512,
                    "sent": "I want to order T-shirts.",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "customize_tshirt",
                        "prob": 0.9762795567512512,
                        "sent": "I want to order T-shirts.",
                    }
                ],
                "negation": {
                    "wordlist": ["hi", ",", "i", "want", "to", "order", "t-shirts"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": ["hi", ",", "I", "want", "to", "order", "T-shirts"],
                    "predicted_clusters": [],
                    "top_spans": [(2, 3), (5, 6)],
                },
                "final_intent": {
                    "intent": "customize_tshirt",
                    "prob": 0.9762795567512512,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "negative",
                    "prob": 0.9797140955924988,
                    "sent": "No",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "negative",
                        "prob": 0.9797140955924988,
                        "sent": "No",
                    }
                ],
                "negation": {"wordlist": ["nothing"], "triplets": [(-1, -1, -1)]},
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
                        "customize",
                        "your",
                        "T-shirts",
                        ".",
                        "What",
                        "text",
                        "do",
                        "you",
                        "want",
                        "to",
                        "print",
                        "on",
                        "the",
                        "front",
                        "side",
                        "of",
                        "the",
                        "T-shirt",
                        "?",
                        "nothing",
                    ],
                    "predicted_clusters": [
                        [(9, 10), (11, 12), (17, 18)],
                        [(11, 13), (26, 28)],
                    ],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 12),
                        (11, 13),
                        (11, 16),
                        (17, 18),
                        (18, 19),
                        (20, 21),
                        (22, 28),
                        (26, 28),
                    ],
                },
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9797140955924988,
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
                    "wordlist": ["``", "big", "brain", "''"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Got",
                        "it",
                        ".",
                        "What",
                        "text",
                        "do",
                        "you",
                        "want",
                        "to",
                        "print",
                        "on",
                        "the",
                        "back",
                        "side",
                        "?",
                        "``",
                        "Big",
                        "Brain",
                        "''",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [
                        (1, 2),
                        (1, 5),
                        (6, 7),
                        (9, 10),
                        (11, 14),
                        (15, 19),
                        (16, 18),
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
                "negation": {
                    "wordlist": ["pink", "sounds", "great"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "OK",
                        ".",
                        "Which",
                        "color",
                        "do",
                        "you",
                        "prefer",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "white",
                        "-",
                        "black",
                        "-",
                        "red",
                        "-",
                        "pink",
                        "-",
                        "yellow",
                        "-",
                        "blue",
                        "-",
                        "purple",
                        "pink",
                        "sounds",
                        "great",
                    ],
                    "predicted_clusters": [[(5, 6), (8, 9)]],
                    "top_spans": [
                        (2, 4),
                        (2, 7),
                        (5, 6),
                        (8, 9),
                        (8, 10),
                        (10, 11),
                        (11, 12),
                        (11, 13),
                        (12, 13),
                        (15, 28),
                        (28, 29),
                        (29, 30),
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
                            "probability": 0.8659403324127197,
                            "token": "unisex?",
                            "span": {"start": 6, "end": 13},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "unisex",
                    "prob": 0.9059597253799438,
                    "sent": "Is it unisex?",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "unisex",
                        "prob": 0.9059597253799438,
                        "sent": "Is it unisex?",
                    }
                ],
                "negation": {
                    "wordlist": ["is", "it", "unisex", "?"],
                    "triplets": [(2, 4, 4)],
                },
                "coref": {
                    "words": [
                        "Wonderful",
                        "choice",
                        ".",
                        "What",
                        "size",
                        "do",
                        "you",
                        "want",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "small",
                        "-",
                        "medium",
                        "-",
                        "large",
                        "-",
                        "extra",
                        "large",
                        "Is",
                        "it",
                        "unisex",
                        "?",
                    ],
                    "predicted_clusters": [[(6, 7), (9, 10)]],
                    "top_spans": [
                        (0, 2),
                        (0, 8),
                        (6, 7),
                        (9, 10),
                        (9, 11),
                        (11, 12),
                        (12, 13),
                        (12, 14),
                        (16, 24),
                        (25, 26),
                        (26, 27),
                    ],
                },
                "final_intent": {
                    "intent": "unisex",
                    "prob": 0.9059597253799438,
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
                    "wordlist": ["i", "prefer", "medium", "size"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Is",
                        "it",
                        "unisex",
                        "?",
                        "I",
                        "prefer",
                        "medium",
                        "size",
                    ],
                    "predicted_clusters": [],
                    "top_spans": [(4, 5), (5, 6), (6, 8)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "change_color",
                    "prob": 0.9282354116439819,
                    "sent": "can I change the color",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "change_color",
                        "prob": 0.9282354116439819,
                        "sent": "can I change the color",
                    }
                ],
                "negation": {
                    "wordlist": ["can", "i", "change", "the", "color", "?"],
                    "triplets": [(-1, -1, -1)],
                },
                "coref": {
                    "words": [
                        "Great",
                        "!",
                        "A",
                        "pink",
                        "medium",
                        "T-shirt",
                        "with",
                        "nothing",
                        "on",
                        "the",
                        "front",
                        "side",
                        "and",
                        "``",
                        "Big",
                        "Brain",
                        "''",
                        "on",
                        "the",
                        "back",
                        "side",
                        ".",
                        "Your",
                        "order",
                        "is",
                        "submitted",
                        ".",
                        "Thank",
                        "you",
                        "!",
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
                        "can",
                        "I",
                        "change",
                        "the",
                        "color",
                        "?",
                    ],
                    "predicted_clusters": [[(28, 29), (37, 38), (42, 43)]],
                    "top_spans": [
                        (2, 21),
                        (2, 24),
                        (9, 12),
                        (9, 21),
                        (13, 17),
                        (13, 21),
                        (18, 21),
                        (22, 23),
                        (22, 24),
                        (25, 26),
                        (28, 29),
                        (32, 40),
                        (34, 35),
                        (37, 38),
                        (39, 40),
                        (42, 43),
                        (43, 44),
                        (44, 46),
                    ],
                },
                "final_intent": {
                    "intent": "change_color",
                    "prob": 0.9282354116439819,
                    "uncertain": False,
                },
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "change_color",
                    "prob": 0.7260535955429077,
                    "sent": "change the color to color",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "change_color",
                        "prob": 0.7260535955429077,
                        "sent": "change the color to color",
                    }
                ],
                "negation": {
                    "wordlist": ["i", "want", "purple"],
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
                        "change",
                        "the",
                        "color",
                        ".",
                        "What",
                        "do",
                        "you",
                        "want",
                        "the",
                        "new",
                        "color",
                        "to",
                        "be",
                        "?",
                        "Your",
                        "choices",
                        "are",
                        "listed",
                        "here",
                        ":",
                        "-",
                        "white",
                        "-",
                        "black",
                        "-",
                        "red",
                        "-",
                        "pink",
                        "-",
                        "yellow",
                        "-",
                        "blue",
                        "-",
                        "purple",
                        "I",
                        "want",
                        "purple",
                    ],
                    "predicted_clusters": [[(9, 10), (17, 18), (23, 24), (43, 44)]],
                    "top_spans": [
                        (3, 4),
                        (8, 9),
                        (9, 10),
                        (10, 11),
                        (11, 13),
                        (11, 16),
                        (11, 22),
                        (17, 18),
                        (20, 21),
                        (23, 24),
                        (23, 25),
                        (26, 27),
                        (26, 28),
                        (27, 28),
                        (30, 43),
                        (43, 44),
                        (44, 45),
                        (45, 46),
                    ],
                },
                "final_intent": {
                    "intent": "change_color",
                    "prob": 0.7260535955429077,
                    "uncertain": False,
                },
            },
        ]

        mocked_func.side_effect = [
            {"success": True, "msg": "Info collected: nothing"},
            {"success": True, "msg": 'Info collected: "Big Brain"'},
            {"success": True, "msg": "Info collected: pink"},
            {"success": True, "msg": "Info collected: medium"},
            {
                "success": True,
                "msg": (
                    "A pink medium T-shirt with nothing "
                    'on the front side and "Big Brain" on '
                    "the back side. Your order is submitted."
                    " Thank you!"
                ),
            },
            {"success": True, "msg": "Info collected: purple"},
            {
                "success": True,
                "msg": (
                    "A purple medium T-shirt with nothing "
                    'on the front side and "Big Brain" on '
                    "the back side. Your order is submitted."
                    " Thank you!"
                ),
            },
        ]

        user_inputs = [
            "hi, I want to order T-shirts",
            "nothing",
            '"Big Brain"',
            "pink sounds great",
            "Is it unisex?",
            "I prefer medium size",
            "can I change the color?",
            "I want purple",
        ]
        target_responses = [
            [
                "customize your T-shirts.",
                "What text do you want to print on the front side of the T-shirt?",
            ],
            ["Got it.", "What text do you want to print on the back side?"],
            [
                "OK. Which color do you prefer?",
                "Your choices are listed here:",
                "- white",
                "- black",
                "- red",
                "- pink",
                "- yellow",
                "- blue",
                "- purple",
            ],
            [
                "Wonderful choice. What size do you want?",
                "Your choices are listed here:",
                "- small",
                "- medium",
                "- large",
                "- extra large",
            ],
            [
                "Yes, it is unisex.",
                "Wonderful choice. What size do you want?",
                "Your choices are listed here:",
                "- small",
                "- medium",
                "- large",
                "- extra large",
            ],
            [
                "Great! A pink medium T-shirt with nothing on the front side",
                'and "Big Brain" on the back side.',
                "Your order is submitted. Thank you!",
                "Is there anything else I can help you with today?",
            ],
            [
                "What do you want the new color to be?",
                "Your choices are listed here:",
                "- white",
                "- black",
                "- red",
                "- pink",
                "- yellow",
                "- blue",
                "- purple",
            ],
            [
                "Definitely. I have changed the color.",
                "A purple medium T-shirt with nothing on the front side",
                'and "Big Brain" on the back side.',
                "Your order is submitted. Thank you! ",
            ],
        ]

        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)

    @patch(
        "Converse.dialog_state_manager.dial_state_manager.StateManager._execute_entity_or_task_function"
    )
    # @patch("Converse.dialog_state_manager.dial_state_manager.ef.collect_info")
    @patch("Converse.dialog_info_layer.dial_info.InfoManager.info_pipeline")
    def test_book_flights(self, mocked_info, mocked_func):
        """
        Unit test for book flights example.
        :param mocked_info:
        :param mocked_func:
        :return:
        """
        dm = Orchestrator(
            response_path="./Converse/bot_configs/book_flights/response_template.yaml",
            policy_path="./Converse/bot_configs/policy_config.yaml",
            task_path="./Converse/bot_configs/book_flights/tasks.yaml",
            entity_path="./Converse/bot_configs/book_flights/entity_config.yaml",
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
                            "label": "LOC",
                            "probability": 0.9781135320663452,
                            "token": "san francisco",
                            "span": {"start": 41, "end": 54},
                        },
                        {
                            "label": "LOC",
                            "probability": 0.9720408916473389,
                            "token": "los angeles",
                            "span": {"start": 58, "end": 69},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9415462017059326,
                            "token": "san francisco",
                            "normalizedValue": "PlaceName:san francisco",
                            "span": {"start": 41, "end": 54},
                        },
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "book_a_flight",
                    "prob": 0.9750511646270752,
                    "sent": "I would like to book a flight",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "book_a_flight",
                        "prob": 0.9750511646270752,
                        "sent": "I would like to book a flight",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "i",
                        "'d",
                        "like",
                        "to",
                        "book",
                        "a",
                        "roundtrip",
                        "flight",
                        "from",
                        "san",
                        "francisco",
                        "to",
                        "los",
                        "angeles",
                        "for",
                        "2",
                        "people",
                        ".",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {
                    "intent": "book_a_flight",
                    "prob": 0.9750511646270752,
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
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "LOC",
                            "probability": 0.9817370176315308,
                            "token": "los angeles",
                            "span": {"end": 11},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.9370951652526855,
                            "token": "los angeles",
                            "normalizedValue": "PlaceName:los angeles",
                            "span": {"end": 11},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["los", "angeles"],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "tomorrow",
                            "normalizedValue": "2021-11-11T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8234410285949707,
                            "token": "tomorrow",
                            "span": {"end": 8},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["tomorrow"], "triplets": [(-1, -1, -1)]},
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "DUCKLING/time",
                            "token": "next Monday",
                            "normalizedValue": "2021-11-15T00:00:00.000Z",
                        },
                        {
                            "label": "DATE",
                            "probability": 0.8042474389076233,
                            "token": "next Monday",
                            "span": {"end": 11},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {
                    "wordlist": ["next", "monday"],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "CARDINAL",
                            "probability": 0.8755253553390503,
                            "token": "2",
                            "span": {"end": 1},
                        },
                        {
                            "label": "AP/LOCATION",
                            "probability": 0.5141411423683167,
                            "token": "2",
                            "normalizedValue": "AddressNumber:2",
                            "span": {"end": 1},
                        },
                    ],
                },
                "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
                "intent_seg": [
                    {"success": False, "intent": "", "prob": 0.0, "sent": ""}
                ],
                "negation": {"wordlist": ["2"], "triplets": [(-1, -1, -1)]},
                "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
            },
            {
                "ner": {"success": True},
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7534171938896179,
                    "sent": "yes please",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7534171938896179,
                        "sent": "yes please",
                    }
                ],
                "negation": {
                    "wordlist": ["economy", "please"],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7534171938896179,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORDINAL",
                            "probability": 0.8426456451416016,
                            "token": "first",
                            "span": {"start": 4, "end": 9},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.71036297082901,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.71036297082901,
                        "sent": "affirmative",
                    }
                ],
                "negation": {
                    "wordlist": ["the", "first", "one", "please"],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.71036297082901,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "PERSON",
                            "probability": 0.9399024844169617,
                            "token": "Ajira",
                            "span": {"end": 5},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "positive",
                    "prob": 0.7666467428207397,
                    "sent": "affirmative",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "positive",
                        "prob": 0.7666467428207397,
                        "sent": "affirmative",
                    }
                ],
                "negation": {"wordlist": ["ajira"], "triplets": [(-1, -1, -1)]},
                "final_intent": {
                    "intent": "positive",
                    "prob": 0.7666467428207397,
                    "uncertain": False,
                },
            },
            {
                "ner": {
                    "success": True,
                    "probabilities": [
                        {
                            "label": "ORG",
                            "probability": 0.9444311261177063,
                            "token": "Salesforce AI Research team's",
                            "span": {"start": 18, "end": 47},
                        }
                    ],
                },
                "intent": {
                    "success": True,
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9626614451408386,
                    "sent": "tell me about Salesforce AI research team",
                },
                "intent_seg": [
                    {
                        "success": True,
                        "intent": "learn_about_salesforce_AI_research",
                        "prob": 0.9626614451408386,
                        "sent": "tell me about Salesforce AI research team",
                    }
                ],
                "negation": {
                    "wordlist": [
                        "tell",
                        "me",
                        "about",
                        "the",
                        "salesforce",
                        "ai",
                        "research",
                        "team",
                        "'s",
                        "projects",
                    ],
                    "triplets": [(-1, -1, -1)],
                },
                "final_intent": {
                    "intent": "learn_about_salesforce_AI_research",
                    "prob": 0.9626614451408386,
                    "uncertain": False,
                },
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
                "final_intent": {
                    "intent": "negative",
                    "prob": 0.9498212933540344,
                    "uncertain": False,
                },
            },
        ]
        mocked_func.side_effect = [
            {"success": True, "msg": "Info collected: san francisco"},
            {"success": True, "msg": "Info collected: los angeles"},
            {"success": True, "msg": "Info collected: 2021-11-11"},
            {"success": True, "msg": "Info collected: 2021-11-15"},
            {"success": True, "msg": "Info collected: 2"},
            {"success": True, "msg": "Info collected: Economy"},
            {
                "success": True,
                "msg": "Let's start with your departing flight. Here are the cheapest flights departing from san francisco to los angeles on 2021-11-11:\nOceanic 815, Depart at 4:16am, 800USD\nAjira 316, Depart at 15:42pm, 1500USD\nQantas 442, Depart at 23:08pm, 2300USD.",
            },
            {"success": True, "msg": "Your departing flight is Oceanic 815. "},
            {
                "success": True,
                "msg": "And here are your returning flights:\nOceanic 443, Depart at 4:16am, 800USD\nAjira 232, Depart at 15:42pm, 1500USD\nQantas 424, Depart at 23:08pm, 2300USD.",
            },
            {"success": True, "msg": "Alright, your returning flight is Ajira 232. "},
        ]
        user_inputs = [
            "I'd like to book a roundtrip flight "
            "from san francisco to los angeles for 2 people.",
            "san francisco",
            "los angeles",
            "tomorrow",
            "next Monday",
            "2",
            "economy please",
            "the first one please",
            "Ajira",
            "tell me about the Salesforce AI Research team's projects",
            "no thanks",
        ]
        target_responses = [
            [
                "I'd be happy to help you book a flight",
                "I got multiple possible answers for origin",
                "san francisco and los angeles",
                "which one did you mean?",
                "Could you walk me through the details?",
            ],
            "Where is the destination?",
            "When will your trip start?",
            "When will your trip end?",
            "How many passengers?",
            "And which fare class? (e.g., Economy, Business, First)",
            [
                "Let's start with your departing flight.",
                "Here are the cheapest flights departing",
                "from san francisco to los angeles on 2021-11-11",
                "Oceanic 815, Depart at 4:16am, 800USD",
                "Ajira 316, Depart at 15:42pm, 1500USD",
                "Qantas 442, Depart at 23:08pm, 2300USD.",
                "Which one do you prefer?",
            ],
            [
                "Your departing flight is Oceanic 815.",
                "And here are your returning flights",
                "Oceanic 443, Depart at 4:16am, 800USD",
                "Ajira 232, Depart at 15:42pm, 1500USD",
                "Qantas 424, Depart at 23:08pm, 2300USD.",
                "Which one do you prefer?",
            ],
            [
                "Alright, your returning flight is Ajira 232.",
                "OK, I'm going to connect you to an agent to process the credit card for privacy reasons.",
                "One moment, please.",
                "Can I assist you with anything else?",
            ],
            [
                "OK, here's what I found - https://einstein.ai/mission.",
                "Can I assist you with anything else?",
            ],
            "Thanks for taking the time to chat!",
        ]

        self.assertEqual(len(user_inputs), len(target_responses))
        for user_input, target in zip(user_inputs, target_responses):
            res = dm.process(user_input, user_input, ctx)
            for target_sent in target:
                self.assertIn(target_sent, res)
