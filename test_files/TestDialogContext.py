# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest

from Converse.dialog_context.dialog_context import DialogContext
from Converse.utils.yaml_parser import load_entity
from Converse.config.task_config import TaskConfig, BotConfig


class TestDialogContext(unittest.TestCase):
    def setUp(self):
        entity_config = load_entity("test_files/test_entity_config.yaml")
        self.dialog_context = DialogContext(
            entity_config=entity_config,
            task_config=TaskConfig("test_files/test_tasks.yaml"),
            bot_config=BotConfig("test_files/test_tasks.yaml"),
        )

    def test_serialization_and_deserialization(self):
        serialized = self.dialog_context.serialize()
        ctx = DialogContext.deserialize(serialized)
        self.assertIsNone(ctx.tree_manager.cur_task)
        self.assertIsNone(ctx.tree_manager.cur_node)
        self.assertIsNone(ctx.tree_manager.cur_entity)

        self.dialog_context.tree_manager.set_task("check_weather")
        self.dialog_context.tree_manager.traverse()
        serialized = self.dialog_context.serialize()
        ctx = DialogContext.deserialize(serialized)
        self.assertEqual(ctx.tree_manager.cur_task, "check_weather")
        self.assertEqual(ctx.tree_manager.cur_node.name, "entity_group_1")
        self.assertEqual(ctx.tree_manager.cur_entity, "zip_code")
