# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
import os

from Converse.dialog_tree.tree_manager import TreeManager
from Converse.config.task_config import TaskConfig


class TestTreeManager(unittest.TestCase):
    def setUp(self):
        self.tree_fname = os.path.join(
            os.path.dirname(__file__), "test_tree_manager.yaml"
        )
        self.tm = TreeManager(task_config=TaskConfig(self.tree_fname))

    def mock_leaf_handler(self, asr_out):
        if asr_out == "yes":
            self.tm.update_entity("True")
        elif asr_out == "no":
            self.tm.update_entity("False", False)

    def test_set_task(self):
        self.tm.set_task("check_order")
        self.assertEqual(self.tm.cur_task, "check_order")
        self.assertIsNone(self.tm.cur_node)
        self.assertIsNone(self.tm.cur_entity)
        self.assertFalse(self.tm.finish)
        self.assertListEqual(self.tm.task_stack, ["check_order"])

        self.tm.set_task("fake_user")
        self.assertEqual(self.tm.cur_task, "fake_user")
        self.assertIsNone(self.tm.cur_node)
        self.assertIsNone(self.tm.cur_entity)
        self.assertFalse(self.tm.finish)
        self.assertListEqual(self.tm.task_stack, ["check_order", "fake_user"])

    def test_traverse_yes(self):
        self.tm.set_task("check_order")
        self.assertEqual(self.tm.prev_tasks_success, [])
        self.assertFalse(self.tm.prev_task_finished)
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_1")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "email_address")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_2")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "zip_code")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertFalse(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["fake_user"])
        self.assertEqual(self.tm.prev_tasks_success, [True])
        self.assertTrue(self.tm.prev_task_finished)
        self.tm.reset_prev_task()

        self.assertEqual(cur_node.name, "entity_group_2")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "test entity a")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_2")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "test entity b")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_3")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "test entity31")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_3")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "test entity32")

        self.mock_leaf_handler("yes")
        cur_node, cur_entity = self.tm.traverse()

        self.assertEqual(cur_node.name, "entity_group_5")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "test entity51")

        self.mock_leaf_handler("yes")
        self.assertIsNone(self.tm.traverse())
        self.assertTrue(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["check_order"])
        self.assertEqual(self.tm.prev_tasks_success, [True])
        self.assertTrue(self.tm.prev_task_finished)

    def test_traverse_no(self):
        self.tm.set_task("check_order")
        cur_node, cur_entity = self.tm.traverse()
        self.assertEqual(cur_node.name, "entity_group_1")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "email_address")

        self.mock_leaf_handler("no")
        self.assertIsNone(self.tm.traverse())
        self.assertTrue(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["fake_user", "check_order"])
        self.assertEqual(self.tm.prev_tasks_success, [False, False])
        self.assertTrue(self.tm.prev_task_finished)

    def test_force_task_finish(self):
        self.tm.set_task("check_order")
        cur_node, cur_entity = self.tm.traverse()
        self.assertEqual(cur_node.name, "entity_group_1")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "email_address")
        self.mock_leaf_handler("yes")
        self.tm.force_finish_task()
        self.assertTrue(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["fake_user", "check_order"])
        self.assertEqual(self.tm.prev_tasks_success, [False, False])
        self.assertTrue(self.tm.prev_task_finished)

    def test_switch_tasks(self):
        # Set task to fake_user
        self.tm.set_task("fake_user")
        cur_node, cur_entity = self.tm.traverse()
        self.assertEqual(cur_node.name, "entity_group_1")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "email_address")
        self.mock_leaf_handler("yes")

        # Switch task to verify_user
        self.tm.set_task("verify_user")
        cur_node, cur_entity = self.tm.traverse()
        self.assertEqual(cur_node.name, "entity_group_1")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "email_address")
        self.mock_leaf_handler("yes")

        # Continue with verify_user task
        cur_node, cur_entity = self.tm.traverse()
        self.assertEqual(cur_node.name, "entity_group_2")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "zip_code")
        self.mock_leaf_handler("yes")

        cur_node, cur_entity = self.tm.traverse()
        # Finished with verify_user & switch back to fake_user task
        self.assertFalse(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["verify_user"])
        self.assertEqual(self.tm.prev_tasks_success, [True])
        self.assertTrue(self.tm.prev_task_finished)
        self.tm.reset_prev_task()

        # Continue with fake_user task
        self.assertEqual(cur_node.name, "entity_group_2")
        self.assertFalse(cur_node.success)
        self.assertEqual(cur_entity, "zip_code")
        self.mock_leaf_handler("yes")

        # Done with fake_user task
        self.assertIsNone(self.tm.traverse())
        self.assertTrue(self.tm.finish)
        self.assertEqual(self.tm.prev_tasks, ["fake_user"])
        self.assertEqual(self.tm.prev_tasks_success, [True])
        self.assertTrue(self.tm.prev_task_finished)

    def test_reset_prev_task(self):
        # set previous task fields
        self.tm.prev_tasks = ["check_task"]
        self.prev_tasks_success = [True]

        # reset previous task fields
        self.tm.reset_prev_task()
        self.assertEqual(self.tm.prev_tasks, [])
        self.assertEqual(self.tm.prev_tasks_success, [])

    def test_entity_with_multiple_usages(self):
        tree_fname = os.path.join(
            os.path.dirname(__file__),
            "test_entity_groups_multiple_time_usage_task.yaml",
        )
        tree_mgr = TreeManager(task_config=TaskConfig(tree_fname))

        tree_mgr.set_task("check_and_update_order")
        tree_mgr.traverse()
        self.assertEqual(tree_mgr.cur_node.name, "entity_group_1")
        self.assertEqual(tree_mgr.cur_entity, "oid")
        tree_mgr.update_entity("1")
        tree_mgr.traverse()
        self.assertFalse(tree_mgr.cur_node.success)
        self.assertEqual(tree_mgr.cur_node.name, "entity_group_1")
        self.assertEqual(tree_mgr.cur_entity, "oid")
        tree_mgr.update_entity("2")
        tree_mgr.traverse()
        self.assertFalse(tree_mgr.cur_node.success)
        self.assertEqual(tree_mgr.cur_node.name, "entity_group_2")
        self.assertEqual(tree_mgr.cur_entity, "oid")
        tree_mgr.update_entity("3")
        tree_mgr.traverse()
        self.assertTrue(tree_mgr.prev_task_finished)
        self.assertEqual(tree_mgr.prev_tasks_success[0], True)


if __name__ == "__main__":
    unittest.main()
