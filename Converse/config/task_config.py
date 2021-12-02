# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from typing import List

from Converse.utils.yaml_parser import (
    load_tasks,
    load_bot_config,
    load_FAQ_config,
)
from Converse.config.config import (
    FixedKeyConfigDictionary,
    ListOfStr,
    ConfigDictionaryOfType,
    DictionaryOfListOfStr,
)
from Converse.entity.entity_manager import EntityMethodConfig


class TaskFinishResponse(FixedKeyConfigDictionary):
    _OPTIONAL_ATTRIBUTES = {
        "success": ListOfStr(),
        "failure": ListOfStr(),
    }


class TaskEntity(FixedKeyConfigDictionary):
    """
    Nested config object within a Task, specified by the key 'entities'
    """

    _REQUIRED_ATTRIBUTES = {
        "function": str,  # function to call
    }

    _OPTIONAL_ATTRIBUTES = {
        "confirm": False,  # confirm the entity with the user
        "confirm_retrieved": True,  # confirm if retrieved from the past
        "prompt": ListOfStr(),  # prompt string list
        "response": ListOfStr(),  # response string list
        "retrieve": True,  # retrieve the entity from history
        "forget": False,  # do not retrieve this entity in the future
        "type": ListOfStr(),
        "methods": EntityMethodConfig(),
        "suggest_value": False,  # whether or not suggest value candidates for picklist
    }

    def __init__(self, task_entity: dict):
        # placeholder for the attributes so that IDE can expect these fields
        self.function = None
        self.confirm = None
        self.confirm_retrieved = None
        self.prompt = None
        self.response = None
        self.retrieve = None
        self.forget = None

        self.type = None
        self.methods = None

        super().__init__(task_entity)


class DictionaryOfTaskEntity(ConfigDictionaryOfType):
    _type = TaskEntity


class Task(FixedKeyConfigDictionary):
    """
    A task yaml is expected to be
    Task: {
        taskName1: Task1,
        taskName2: Task2,
        ...
    }
    where each task name is mapped to an instance of this object
    """

    _REQUIRED_ATTRIBUTES = {
        "description": str,  # description
    }

    _OPTIONAL_ATTRIBUTES = {
        "samples": ListOfStr(),  # example intents for this task
        "entities": DictionaryOfTaskEntity(),  # entities that are needed for this task
        "entity_groups": DictionaryOfListOfStr(),  # groups of entities for this task
        "success": {},  # task action
        "repeat": False,  # whether or not to repeat the task after success
        "max_turns": float("infinity"),  # number of turns allowed for this task
        "finish_response": TaskFinishResponse(),  # response to print after success
        # handles all the collected entity info after success
        "task_finish_function": str(),
        "repeat_response": ListOfStr(),
        "confirm": False,  # not sure if it is being used anymore
    }

    def __init__(self, task_attributes: dict):
        """
        Args:
            task_attributes: task attributes for each task as defined in the task yaml
        """
        # placeholder for the attributes so that IDE can expect these fields
        self.description = None
        self.samples = None
        self.entities = None
        self.entity_groups = None
        self.success = None
        self.repeat = None
        self.max_turns = None
        self.finish_response = None
        self.repeat_response = None
        self.task_finish_function = None
        self.confirm = None

        if "max_turns" in task_attributes and not task_attributes["max_turns"]:
            task_attributes["max_turns"] = float("infinity")

        super().__init__(task_attributes)
        self.verify_entity_groups()
        self.verify_success_node(self.success)

    def verify_entity_groups(self):
        if self.entity_groups:
            for entity_group in self.entity_groups:
                for entity in self.entity_groups[entity_group]:
                    if entity not in self.entities:
                        raise ValueError(f"Unknown entity: {entity}")

    def verify_success_node(self, node):
        keys = {
            "AND",
            "OR",
            "TASK",
            "INFORM",
            "INSERT",
            "SIMPLE",
            "QUERY",
            "UPDATE",
            "VERIFY",
            "API",
        }

        if not node:
            return
        elif isinstance(node, list):
            for n in node:
                self.verify_success_node(n)
        elif isinstance(node, dict):
            for key, value in node.items():
                self.verify_success_node(key)
                if key != "TASK":  # task names are not available
                    self.verify_success_node(value)
        elif isinstance(node, str):
            node = node.split("#")[0]  # in case of "entity_group_1#2"
            if node not in self.entity_groups and node not in keys:
                raise ValueError(f"Unknown key: {node}")


class TaskConfig(ConfigDictionaryOfType):
    """
    Wrapper function to load config directly from the yaml file
    """

    _type = Task

    def __init__(self, taskYamlFile: str):
        dictionary = load_tasks(taskYamlFile)
        super().__init__(dictionary)

    def get_descriptions(self) -> List[str]:
        return [
            value.description
            for key, value in self.items()
            if key not in {"positive", "negative"} and value.samples
        ]


class BotConfig(FixedKeyConfigDictionary):
    """
    Wrapper function to load bot config from the tasks.yaml file
    """

    _OPTIONAL_ATTRIBUTES = {
        "text_bot": True,
        "bot_name": "your Converse bot",
    }

    def __init__(self, taskYamlFile: str):
        self.bot_name = None
        self.text_bot = None
        dictionary = load_bot_config(taskYamlFile)
        super().__init__(dictionary)


class FAQ(FixedKeyConfigDictionary):
    """
    A FAQ yaml is expected to be
    FAQ: {
        FAQName1: FAQ1,
        FAQName2: FAQ2,
        ...
    }
    where each FAQ name is mapped to an instance of this object
    """

    _REQUIRED_ATTRIBUTES = {
        "samples": ListOfStr,
        "answers": ListOfStr,
        "question_match_options": str,
    }

    def __init__(self, faq_attributes: dict):
        self.samples = None
        self.answers = None
        self.question_match_options = None
        super().__init__(faq_attributes)


class FAQConfig(ConfigDictionaryOfType):
    """
    Wrapper function to load config directly from the yaml file
    """

    _type = FAQ

    def __init__(self, taskYamlFile: str):
        dictionary = load_FAQ_config(taskYamlFile)
        super().__init__(dictionary)
