# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
from unittest.mock import patch

from Converse.dialog_info_layer.dial_info import InfoManager
from Converse.utils.yaml_parser import load_entity
from Converse.config.task_config import TaskConfig, BotConfig
from Converse.dialog_context.dialog_context import DialogContext


class TestInfoManager(unittest.TestCase):
    def setUp(self):
        entity_config = load_entity("test_files/test_entity_config.yaml")
        self.dialog_context = DialogContext(
            entity_config=entity_config,
            task_config=TaskConfig("./test_files/test_tasks.yaml"),
            bot_config=BotConfig("./test_files/test_tasks.yaml"),
        )

    @patch("Converse.nlu.intent_converse.client.IntentDetection.__call__")
    @patch("Converse.nlu.ner_converse.client.NER.__call__")
    @patch("Converse.nlu.negation_detection.negation_v2.NegationDetection.__call__")
    def test_info_pipeline_no_coref(self, mock_negation, mock_ner, mock_intent):
        utt1 = (
            "The bike is in my father's favorite color, "
            "I will buy it as a gift for him."
        )
        utt2 = "I bought it from your store yesterday, but I don't like it."
        res1 = {
            "ner": {"success": True},
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "negation": {
                "wordlist": [
                    "the",
                    "bike",
                    "is",
                    "in",
                    "my",
                    "father",
                    "'s",
                    "favorite",
                    "color",
                    ",",
                    "i",
                    "will",
                    "buy",
                    "it",
                    "as",
                    "a",
                    "gift",
                    "for",
                    "him",
                    ".",
                ],
                "triplets": [(-1, -1, -1)],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        res2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "DUCKLING/time",
                        "token": "yesterday",
                        "normalizedValue": "2021-01-18T00:00:00.000-08:00",
                    },
                    {
                        "label": "DATE",
                        "probability": 0.9255957,
                        "token": "yesterday,",
                        "span": {"start": 28, "end": 38},
                    },
                ],
            },
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "negation": {
                "wordlist": [
                    "i",
                    "bought",
                    "it",
                    "from",
                    "your",
                    "store",
                    "yesterday",
                    ",",
                    "but",
                    "i",
                    "do",
                    "n't",
                    "like",
                    "it",
                    ".",
                ],
                "triplets": [(11, 12, 13)],
            },
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        remove_negation_1 = (
            "The bike is in my father 's favorite color , "
            "I will buy it as a gift for him ."
        )
        remove_negation_2 = (
            "i bought it from your store yesterday , but i do  like it ."
        )
        mock_negation.side_effect = [
            {
                "wordlist": [
                    "the",
                    "bike",
                    "is",
                    "in",
                    "my",
                    "father",
                    "'s",
                    "favorite",
                    "color",
                    ",",
                    "i",
                    "will",
                    "buy",
                    "it",
                    "as",
                    "a",
                    "gift",
                    "for",
                    "him",
                    ".",
                ],
                "triplets": [(-1, -1, -1)],
            },
            {
                "wordlist": [
                    "i",
                    "bought",
                    "it",
                    "from",
                    "your",
                    "store",
                    "yesterday",
                    ",",
                    "but",
                    "i",
                    "do",
                    "n't",
                    "like",
                    "it",
                    ".",
                ],
                "triplets": [(11, 12, 13)],
            },
        ]
        mock_ner.side_effect = [
            {"success": True},
            {
                "success": True,
                "probabilities": [
                    {
                        "label": "DUCKLING/time",
                        "token": "yesterday",
                        "normalizedValue": "2021-01-18T00:00:00.000-08:00",
                    },
                    {
                        "label": "DATE",
                        "probability": 0.9255957,
                        "token": "yesterday,",
                        "span": {"start": 28, "end": 38},
                    },
                ],
            },
        ]
        mock_intent.return_value = {
            "success": False,
            "intent": "",
            "prob": 0.0,
            "sent": "",
        }
        im = InfoManager(
            "./Converse/bot_configs/dial_info_config.yaml",
            task_config=TaskConfig("./test_files/test_tasks.yaml"),
        )
        res = im.info_pipeline(utt1, utt1, self.dialog_context)
        rn_1 = self.dialog_context.user_history.messages_buffer[
            -1
        ].text_with_negation_words_removed
        rc_1 = self.dialog_context.user_history.messages_buffer[-1].utt_replaced_coref
        self.assertDictEqual(res1, res)
        self.assertIn(rn_1.lower(), remove_negation_1.lower())
        res = im.info_pipeline(utt2, utt2, self.dialog_context)
        rn_2 = self.dialog_context.user_history.messages_buffer[
            -1
        ].text_with_negation_words_removed
        rc_2 = self.dialog_context.user_history.messages_buffer[-1].utt_replaced_coref
        self.assertDictEqual(res2, res)
        self.assertIn(rn_2.lower(), remove_negation_2.lower())

    @patch("Converse.nlu.intent_converse.client.IntentDetection.__call__")
    @patch("Converse.nlu.ner_converse.client.NER.__call__")
    def test_info_pipeline_without_coref_and_negation(self, mock_ner, mock_intent):
        utt1 = (
            "The bike is in my father's favorite color, "
            "I will buy it as a gift for him."
        )
        utt2 = "I bought it from your store yesterday, but I don't like it."
        res1 = {
            "ner": {"success": True},
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        res2 = {
            "ner": {
                "success": True,
                "probabilities": [
                    {
                        "label": "DUCKLING/time",
                        "token": "yesterday",
                        "normalizedValue": "2021-01-18T00:00:00.000-08:00",
                    },
                    {
                        "label": "DATE",
                        "probability": 0.9255957,
                        "token": "yesterday,",
                        "span": {"start": 28, "end": 38},
                    },
                ],
            },
            "intent": {"success": False, "intent": "", "prob": 0.0, "sent": ""},
            "intent_seg": [{"success": False, "intent": "", "prob": 0.0, "sent": ""}],
            "final_intent": {"intent": "", "prob": 0.0, "uncertain": False},
        }
        remove_negation_1 = (
            "The bike is in my father 's favorite color , "
            "I will buy it as a gift for him ."
        )
        replace_coref_1 = (
            "The bike is in my father 's favorite color , "
            "I will buy it as a gift for him ."
        )
        remove_negation_2 = (
            "I bought it from your store yesterday , but I do n't like it ."
        )
        replace_coref_2 = (
            "I bought it from your store yesterday , but I do n't like it ."
        )

        mock_ner.side_effect = [
            {"success": True},
            {
                "success": True,
                "probabilities": [
                    {
                        "label": "DUCKLING/time",
                        "token": "yesterday",
                        "normalizedValue": "2021-01-18T00:00:00.000-08:00",
                    },
                    {
                        "label": "DATE",
                        "probability": 0.9255957,
                        "token": "yesterday,",
                        "span": {"start": 28, "end": 38},
                    },
                ],
            },
        ]
        mock_intent.return_value = {
            "success": False,
            "intent": "",
            "prob": 0.0,
            "sent": "",
        }
        im = InfoManager(
            "./test_files/infoconfig_without_coref_and_negation.yaml",
            task_config=TaskConfig("./test_files/test_tasks.yaml"),
        )
        res = im.info_pipeline(utt1, utt1, self.dialog_context)
        rn_1 = self.dialog_context.user_history.messages_buffer[
            -1
        ].text_with_negation_words_removed
        rc_1 = self.dialog_context.user_history.messages_buffer[-1].utt_replaced_coref
        self.assertDictEqual(res1, res)
        self.assertIn(rn_1, remove_negation_1)
        self.assertIn(rc_1, replace_coref_1)
        res = im.info_pipeline(utt2, utt2, self.dialog_context)
        rn_2 = self.dialog_context.user_history.messages_buffer[
            -1
        ].text_with_negation_words_removed
        rc_2 = self.dialog_context.user_history.messages_buffer[-1].utt_replaced_coref
        self.assertDictEqual(res2, res)
        self.assertIn(rn_2, remove_negation_2)
        self.assertIn(rc_2, replace_coref_2)


if __name__ == "__main__":
    unittest.main()
