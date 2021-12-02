# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
import os

from Converse.response.response import Response
from Converse.entity.entity_manager import EntityManager
from Converse.config.task_config import TaskConfig, BotConfig


class TestResponse(unittest.TestCase):
    def setUp(self):
        self.task_filename = os.path.join(
            os.path.dirname(__file__), "test_response_task.yaml"
        )
        self.entity_filename = os.path.join(
            os.path.dirname(__file__), "test_entity_config.yaml"
        )
        self.response_template_filename = os.path.join(
            os.path.dirname(__file__), "test_response_template.yaml"
        )

        self.response = Response(
            template=self.response_template_filename,
            task_config=TaskConfig(self.task_filename),
            bot_config=BotConfig(self.task_filename),
            entity_manager=EntityManager(self.entity_filename),
        )

    def test_task_finish_response_empty_tasks(self):
        self.assertEqual(self.response.task_finish_response([], [], ""), "")

    def test_task_finish_response_task_not_in_task_config(self):
        self.assertEqual(
            self.response.task_finish_response(["check_user"], [True], ""), ""
        )

    def test_task_finish_response_no_task_response_configured_task_success(self):
        self.assertEqual(
            self.response.task_finish_response(["verify_user"], [True], ""),
            "Your request for verify that you are in our database has been completed.",
        )

    def test_task_finish_response_no_task_response_configured_task_failure(self):
        self.assertEqual(
            self.response.task_finish_response(["verify_user"], [False], ""),
            "Sorry, I cannot help to finish verify that you are in our database.",
        )

    def test_task_finish_response_both_task_response_configured_task_success(self):
        self.assertEqual(
            self.response.task_finish_response(["check_order"], [True], ""),
            "check_order succeeded.",
        )

    def test_task_finish_response_both_task_response_configured_task_failure(self):
        self.assertEqual(
            self.response.task_finish_response(["check_order"], [False], ""),
            "check_order failed.",
        )

    def test_task_finish_response_task_success_with_task_finish_func_info(self):
        self.assertEqual(
            self.response.task_finish_response(
                ["check_order"], [True], "I am glad I can help."
            ),
            "check_order succeeded. I am glad I can help.",
        )

    def test_task_finish_response_task_failure_with_task_finish_func_info(self):
        self.assertEqual(
            self.response.task_finish_response(
                ["check_order"], [False], "Please try again."
            ),
            "check_order failed. Please try again.",
        )

    def test_task_finish_response_only_task_success_response_configured_task_success(
        self,
    ):
        self.assertEqual(
            self.response.task_finish_response(["fake_user"], [True], ""),
            "fake_user succeeded",
        )

    def test_task_finish_response_only_task_success_response_configured_task_failure(
        self,
    ):
        self.assertEqual(
            self.response.task_finish_response(["fake_user"], [False], ""),
            "Sorry, I cannot help to finish pull up your account.",
        )

    def test_task_finish_response_only_task_failure_response_configured_task_success(
        self,
    ):
        self.assertEqual(
            self.response.task_finish_response(["update_order"], [True], ""),
            "Your request for add more to your order has been completed.",
        )

    def test_task_finish_response_only_task_failure_response_configured_task_failure(
        self,
    ):
        self.assertEqual(
            self.response.task_finish_response(["update_order"], [False], ""),
            "update_order failed",
        )

    def test_task_finish_response_pick_zeroth_task(self):
        self.assertEqual(
            self.response.task_finish_response(
                ["check_order", "update_order"], [False, False], ""
            ),
            "check_order failed.",
        )

    def test_task_repeat_response_no_repeat_response_configured(self):
        self.assertEqual(
            self.response.task_repeat_response("check_order"),
            "Would you like to repeat check your order status?",
        )

    def test_task_repeat_response_repeat_response_configured(self):
        self.assertEqual(
            self.response.task_repeat_response("update_order"), "update_order repeat"
        )

    def test_greeting(self):
        """
        Test that the bot name used in the greeting is configured using the
        response_template.yaml file.
        """
        self.assertEqual(
            self.response.greeting(),
            "Hi there, I am the digital assistant for Northern Trail Information "
            "Center. What can I do for you?",
        )

    def test_greeting_with_different_bot_name(self):
        """
        Test that the bot name used in the greeting is configured using the
        response_template.yaml file and not hard coded. Since we are changing the
        bot name in the response_template.yaml, we expect to see this change reflected
        in the bot's greeting.
        """
        self.task_filename = os.path.join(
            os.path.dirname(__file__), "test_response_task_different_bot_name.yaml"
        )
        self.entity_filename = os.path.join(
            os.path.dirname(__file__), "test_entity_config.yaml"
        )
        self.response_template_filename = os.path.join(
            os.path.dirname(__file__), "test_response_template.yaml"
        )
        self.response = Response(
            template=self.response_template_filename,
            task_config=TaskConfig(self.task_filename),
            bot_config=BotConfig(self.task_filename),
            entity_manager=EntityManager(self.entity_filename),
        )
        self.assertEqual(
            self.response.greeting(),
            "Hi there, I am the digital assistant for Inn: The Cloud. "
            "What can I do for you?",
        )

    def test_suggest_entity_value(self):
        """
        Test that the if we want to suggest entity values when generating entity
        prompt. We can set True or False in entity_config.yaml. When the entity
        methods contains candidate values, we can suggest those values to the
        user to help user understand what he or she needs to answer.
        """
        self.task_filename = os.path.join(
            os.path.dirname(__file__), "test_suggest_entity_value_task_config.yaml"
        )
        self.entity_filename = os.path.join(
            os.path.dirname(__file__), "test_suggest_entity_value_entity_config.yaml"
        )
        self.response_template_filename = os.path.join(
            os.path.dirname(__file__), "test_response_template.yaml"
        )
        self.response = Response(
            template=self.response_template_filename,
            task_config=TaskConfig(self.task_filename),
            bot_config=BotConfig(self.task_filename),
            entity_manager=EntityManager(self.entity_filename),
        )
        entity_prompt = self.response.ask_info("health_appointment", "department")
        target_response = [
            "Which department do you want to make the appointment with?\n",
            "Your choices are listed here:\n",
            "- ICU\n",
            "- Elderly services\n",
            "- Diagnostic Imaging\n",
            "- General Surgery\n",
            "- Neurology\n",
            "- Microbiology\n",
            "- Nutrition and Dietetics",
        ]
        for tgt in target_response:
            self.assertIn(tgt, entity_prompt)


if __name__ == "__main__":
    unittest.main()
