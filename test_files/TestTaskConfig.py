# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest

from Converse.config.task_config import TaskConfig, BotConfig


class TestConfigTask(unittest.TestCase):
    def setUp(self):
        self.task_config = TaskConfig("test_files/test_task_tree.yaml")
        self.bot_config = BotConfig("test_files/test_task_tree.yaml")

    def test_task_config(self):
        self.assertEqual(len(self.task_config), 2)
        expected_tasks = ["user_login", "user_security_question"]
        expected_descriptions = {
            "user_login": "ask user name and password to log in",
            "user_security_question": "ask user securities question to verify",
        }
        expected_turns = {"user_login": 5, "user_security_question": 3}

        for idx, task_name in enumerate(self.task_config):
            task = self.task_config[task_name]
            self.assertIn(task_name, expected_tasks)
            self.assertEqual(task.description, expected_descriptions[task_name])
            self.assertEqual(task.max_turns, expected_turns[task_name])

    def test_bot_config(self):
        """
        the default value of bot config:
        bot_name: your Converse bot
        text_bot: True
        """
        self.assertEqual(self.bot_config.bot_name, "your Converse bot")
        self.assertEqual(self.bot_config.text_bot, True)


if __name__ == "__main__":
    unittest.main()
