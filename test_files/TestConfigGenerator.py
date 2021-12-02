# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
import os
from Converse.utils.yaml_parser import load_yaml
from Converse.utils.config_yaml_generator import YamlGenerator


class TestResponse(unittest.TestCase):
    def setUp(self):
        self.task_filename = os.path.join(
            os.path.dirname(__file__), "test_config_generator_task.yaml"
        )
        self.entity_filename = os.path.join(
            os.path.dirname(__file__), "test_config_generator_entity.yaml"
        )

        self.target_task_dict = load_yaml(self.task_filename)
        self.target_entity_dict = load_yaml(self.entity_filename)
        self.config_generator = YamlGenerator(os.path.dirname(__file__))

    def test_generating_task_entity_yamls(self):
        """
        In this unit test, we try to set bot name,  add 2 tasks and
        their entities, then we compare generated task dict and entity
        dict with predefined targets.
        """
        self.config_generator.add_bot_name("test_bot")
        self.config_generator.add_task("online_shopping")
        self.config_generator.add_entity("online_shopping", "entity_1")
        self.config_generator.add_entity("online_shopping", "entity_2")
        self.config_generator.add_task("online_health")
        self.config_generator.add_entity("online_health", "entity_1")
        self.config_generator.add_entity("online_health", "entity_2")
        self.config_generator.add_entity("online_health", "entity_3")

        self.assertDictEqual(self.config_generator.task_dict, self.target_task_dict)
        self.assertDictEqual(self.config_generator.entity_dict, self.target_entity_dict)
