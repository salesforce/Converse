# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import os

from Converse.utils.yaml_parser import load_yaml, save_yaml


class YamlGenerator:
    def __init__(
        self,
        yaml_dir="./Converse/bot_configs",
    ):
        self.task_yaml_path = yaml_dir.rstrip("/") + "/tasks.yaml"
        self.entity_yaml_path = yaml_dir.rstrip("/") + "/entity_config.yaml"
        if os.path.exists(self.task_yaml_path) and os.path.exists(
            self.entity_yaml_path
        ):
            self.task_dict = load_yaml(self.task_yaml_path)
            self.entity_dict = load_yaml(self.entity_yaml_path)
        else:
            self.task_dict = {
                "Bot": {
                    "text_bot": True,
                    "bot_name": None,
                },
                "Task": {
                    "positive": {
                        "description": "polarity",
                        "samples": [
                            "Yes",
                            "Sure",
                            "correct",
                            "No problem",
                            "that's right",
                            "yes please",
                            "affirmative",
                            "roger that",
                        ],
                    },
                    "negative": {
                        "description": "polarity",
                        "samples": [
                            "No",
                            "Sorry",
                            "No, I don't think so.",
                            "I dont know",
                            "It's not right",
                            "Not exactly",
                            "Nothing to do",
                            "I forgot my",
                            "I forgot it",
                            "I don't want to tell you",
                        ],
                    },
                },
            }
            self.entity_dict = {"Entity": {}}

    def add_bot_name(self, bot_name):
        if bot_name:
            self.task_dict["Bot"]["bot_name"] = bot_name

    def add_task(self, task_name):
        if task_name not in self.task_dict["Task"]:
            self.task_dict["Task"][task_name] = dict()
            self.task_dict["Task"][task_name]["description"] = None
            self.task_dict["Task"][task_name]["samples"] = list()
            self.task_dict["Task"][task_name]["entities"] = dict()
            self.task_dict["Task"][task_name]["entity_groups"] = dict()
            self.task_dict["Task"][task_name]["entity_groups"][
                "entity_group_1"
            ] = list()
            self.task_dict["Task"][task_name]["success"] = dict()
            self.task_dict["Task"][task_name]["success"]["AND"] = list()
            self.task_dict["Task"][task_name]["finish_response"] = dict()
            self.task_dict["Task"][task_name]["finish_response"]["success"] = list()
            self.task_dict["Task"][task_name]["finish_response"]["failure"] = list()
            self.task_dict["Task"][task_name]["repeat"] = False
            self.task_dict["Task"][task_name]["repeat_response"] = list()
            self.task_dict["Task"][task_name]["task_finish_function"] = None
            self.task_dict["Task"][task_name]["max_turns"] = 10

    def add_entity(self, task_name, entity_name):
        if entity_name not in self.task_dict["Task"][task_name]["entities"]:
            self.task_dict["Task"][task_name]["entities"][entity_name] = dict()
            self.task_dict["Task"][task_name]["entities"][entity_name][
                "function"
            ] = None
            self.task_dict["Task"][task_name]["entities"][entity_name][
                "confirm"
            ] = False
            self.task_dict["Task"][task_name]["entities"][entity_name][
                "prompt"
            ] = list()
            self.task_dict["Task"][task_name]["entities"][entity_name][
                "response"
            ] = list()

        if entity_name not in self.entity_dict["Entity"]:
            self.entity_dict["Entity"][entity_name] = dict()
            self.entity_dict["Entity"][entity_name]["type"] = None
            self.entity_dict["Entity"][entity_name]["methods"] = dict()

    def add_faq(self, faq_name: str):
        if "FAQ" not in self.task_dict:
            self.task_dict["FAQ"] = dict()
        self.task_dict["FAQ"][faq_name] = dict()
        self.task_dict["FAQ"][faq_name]["samples"] = []
        self.task_dict["FAQ"][faq_name]["answers"] = []
        self.task_dict["FAQ"][faq_name]["question_match_options"] = []

    def generate_yaml_file(self):
        save_yaml(self.task_dict, self.task_yaml_path)
        save_yaml(self.entity_dict, self.entity_yaml_path)


def receive_user_input(config_generator: YamlGenerator):
    bot_name = input("Input bot name: ")
    config_generator.add_bot_name(bot_name)
    while True:
        task_name = input("Input a task name: ")
        if task_name:
            config_generator.add_task(task_name)
            entity_names = input(
                "Input entity names, separated by '||' (entity_1||entity_2||entity_3): "
            ).split("||")
            for entity in entity_names:
                if entity:
                    config_generator.add_entity(task_name, entity)
            continue_input = input("Continue adding tasks? (Input yes or no): ")
            if continue_input == "no":
                faq = input("Do you want to also add FAQs? (Input yes or no): ")
                if faq == "yes":
                    faq_names = input(
                        "Input FAQ names, separated by '||' (FAQ_1||FAQ_2||FAQ_3): "
                    ).split("||")
                    for faq_name in faq_names:
                        config_generator.add_faq(faq_name)
                    break
                else:
                    break
    config_generator.generate_yaml_file()


if __name__ == "__main__":
    yaml_dir = input("Input yaml dir, default is Converse/bot_configs: ")
    if yaml_dir:
        config_generator = YamlGenerator(yaml_dir)
    else:
        config_generator = YamlGenerator()
    receive_user_input(config_generator)
