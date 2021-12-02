# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
import os

from Converse.dialog_tree.dial_tree import TaskTree
from Converse.config.task_config import TaskConfig


class TestTaskTree(unittest.TestCase):
    def setUp(self):

        self.tree_fname = os.path.join(os.path.dirname(__file__), "test_task_tree.yaml")
        self.tree = TaskTree(TaskConfig(self.tree_fname))
        self.recursion_error_message = str(
            "Task dependency cycle detected. Please check your task configuration file!"
        )

    def test_simple_build_subtree(self):

        self.tree.build_subtree("user_security_question")

        self.assertFalse(self.tree.root.success)
        self.assertEqual(self.tree.root.name, "root")
        self.assertSetEqual(
            set(self.tree.root.child.keys()), set(["user_security_question"])
        )

        self.assertDictEqual(
            self.tree.tree_paths,
            {
                "user_security_question": {
                    "0": {"E_hometown": {"hometown": "entity"}},
                    "1": {"E_best_friend": {"best_friend": "entity"}},
                }
            },
        )
        self.assertListEqual(self.tree.task_order, ["user_security_question"])
        self.assertSetEqual(self.tree.task_set, set(["user_security_question"]))

    def test_complex_build_subtree(self):

        self.tree.build_subtree("user_login")
        self.assertFalse(self.tree.root.success)
        self.assertEqual(self.tree.root.name, "root")
        self.assertSetEqual(
            set(self.tree.root.child.keys()),
            set(["user_login", "user_security_question"]),
        )

        self.assertDictEqual(
            self.tree.tree_paths,
            {
                "user_login": {
                    "0": {"E_user": {"user": "entity"}},
                    "1": {"E_password": {"password": "entity"}},
                    "2": {"user_security_question": "task"},
                },
                "user_security_question": {
                    "0": {"E_hometown": {"hometown": "entity"}},
                    "1": {"E_best_friend": {"best_friend": "entity"}},
                },
            },
        )

        self.assertListEqual(
            self.tree.task_order, ["user_login", "user_security_question"]
        )
        self.assertSetEqual(
            self.tree.task_set, set(["user_login", "user_security_question"])
        )

    def test_task_tree_validator_1(self):
        """
        This function tests whether the task tree data structure can detect cycle
        from the starting task to itself when building sub-tree.
        """
        tree_fname = os.path.join(
            os.path.dirname(__file__), "test_task_tree_validator_1.yaml"
        )
        tree = TaskTree(TaskConfig(tree_fname))
        try:
            tree.build_subtree("task_a")
        except RecursionError as e:
            self.assertEqual(str(e), self.recursion_error_message)

    def test_task_tree_validator_2(self):
        """
        This function tests whether the task tree data structure can detect
        cycle from a sub-task when building sub-tree.
        """
        tree_fname = os.path.join(
            os.path.dirname(__file__), "test_task_tree_validator_2.yaml"
        )
        tree = TaskTree(TaskConfig(tree_fname))
        try:
            tree.build_subtree("task_a")
        except RecursionError as e:
            self.assertEqual(str(e), self.recursion_error_message)

    def test_task_tree_validator_3(self):
        """
        This function tests whether the task tree data structure can build
        task tree when we remove the cycle from test_task_tree_validator_1.
        """
        tree_fname = os.path.join(
            os.path.dirname(__file__), "test_task_tree_validator_3.yaml"
        )
        tree = TaskTree(TaskConfig(tree_fname))
        tree.build_subtree("task_a")


if __name__ == "__main__":
    unittest.main()
