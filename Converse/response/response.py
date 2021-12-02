# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from Converse.utils.yaml_parser import load_response
from Converse.entity.entity_manager import EntityManager
from Converse.config.task_config import TaskConfig, BotConfig
from random import choice


class Response:
    def __init__(
        self,
        template: str,
        task_config: TaskConfig,
        bot_config: BotConfig,
        entity_manager: EntityManager,
        user_name="",
    ):
        self._responses = load_response(template)
        self.bot_name = bot_config.bot_name
        self.user_name = user_name
        self.personality = None
        self.follow_up = False
        self.task_config = task_config
        self.entity_manager = entity_manager

    def confirm_user(self):
        if not self.user_name:
            res = choice(self._responses["greetings"]["unknown"]).replace(
                "<bot name>", self.bot_name
            )
        else:
            res = choice(self._responses["greetings"]["known"]).replace(
                "<User>", self.user_name
            )
        return res

    def greeting(self):
        return (
            choice(self._responses["greetings"]["start"])
            .replace("<bot name>", self.bot_name)
            .replace("<user name>", "there" if self.user_name == "" else self.user_name)
        )

    def goodbye(self):
        return choice(self._responses["goodbye"])

    def okay(self):
        return choice(self._responses["okay"])

    def take_time(self):
        return choice(self._responses["take_time"])

    def let_me_know(self):
        return choice(self._responses["let_me_know"])

    def recommend(self, task):
        return choice(self._responses["recommend"]).replace("<Task>", task)

    def forward_to_human(self):
        return choice(self._responses["forward_to_human"])

    def got_intent(self, task, first=True):
        if first:
            return choice(self._responses["got_intent_first"]).replace("<Task>", task)
        else:
            return choice(self._responses["got_intent_middle"]).replace("<Task>", task)

    def task_repeat_response(self, task):
        """
        Generates a response to ask the user if they would like to repeat the previous
        task. This function will return a task specific response if it is available
        (configured in tasks.yaml), otherwise it will return a generic response
        (configured in response_template.yaml).

        Args:
            task: name of task to repeat (str)

        Return:
            a question to ask the user if they would like to repeat the given task (str)
        """
        if self.task_config[task].repeat_response:
            return choice(self.task_config[task].repeat_response)
        else:
            return choice(self._responses["task_repeat_response"]).replace(
                "<Task>", self.task_config[task].description
            )

    def got_intent_2(self, task):
        return choice(self._responses["got_intent_2"]).replace("<Task>", task)

    def got_sub_task(self, task):
        return choice(self._responses["got_sub_task"]).replace("<Task>", task)

    def confirm_intent(self, task):
        return choice(self._responses["confirm_intent"]).replace("<Task>", task)

    def got_invalid_request(self):
        return choice(self._responses["got_invalid_request"])

    def ask_info(self, task, entity):
        if (
            self.task_config
            and task in self.task_config
            and entity in self.task_config[task].entities
            and self.task_config[task].entities[entity].prompt
            and self.task_config[task].entities[entity].prompt[0]
        ):
            res_tmp = choice(self.task_config[task].entities[entity].prompt)
        else:
            res_tmp = (
                choice(self._responses["ask_info"])
                .replace("<Info>", entity)
                .replace("_", " ")
            )
        if self.entity_manager.suggest_entity_value(entity):
            extraction_methods = self.entity_manager.get_extraction_methods(entity)
            entity_values = []
            for method, value in extraction_methods.items():
                if method == "fuzzy_matching":
                    entity_values.extend(value)
            if entity_values:
                res_tmp += "\n" + choice(self._responses["suggest_entity_value"])
                for i in range(len(entity_values)):
                    res_tmp += "- " + str(entity_values[i]) + "\n"
        return res_tmp.strip()

    def entity_response(self, task, entity, info):
        if (
            task
            and entity
            and task in self.task_config
            and entity in self.task_config[task].entities
            and self.task_config[task].entities[entity]["response"]
            and self.task_config[task].entities[entity]["response"][0]
        ):
            return choice(self.task_config[task].entities[entity]["response"]).replace(
                "<info>", info
            )
        else:
            return ""

    def task_finish_response(self, tasks, tasks_success, info=""):
        """
        Generates a response for when a task is finished. If a task specific response
        is configured in tasks.yaml, then it will choose a task specific response based
        on whether the task succeeded or failed. Otherwise, it will return a generic
        response that is configured in response_template.yaml.

        Args:
            tasks: A list of names of finished tasks (str)
            tasks_success: A list of booleans that is the same length as prev_tasks
              where an entry in the list is True if the task at the same index in tasks
              finished successfully and False otherwise.
            info: A string contains the return value of task finish function.

        Return: a response based on whether the finished task succeeded or failed.
        """
        if not tasks:
            return ""
        assert len(tasks) == len(tasks_success), (
            "tasks and tasks_success should have the same length."
            + "tasks has a length of {} and tasks_success has a length of {}".format(
                len(tasks), len(tasks_success)
            )
        )
        task = tasks[0]
        task_success = tasks_success[0]
        if task in self.task_config:
            task_description = self.task_config[task].description
            if task_success:
                if self.task_config[task].finish_response.success:
                    return (
                        choice(self.task_config[task].finish_response["success"])
                        .replace("<info>", info)
                        .strip()
                    )
                else:
                    return choice(
                        self._responses["task_finish_response"]["success"]
                    ).replace("<Task>", task_description)
            else:
                if self.task_config[task].finish_response.failure:
                    return (
                        choice(self.task_config[task].finish_response["failure"])
                        .replace("<info>", info)
                        .strip()
                    )
                else:
                    return choice(
                        self._responses["task_finish_response"]["failure"]
                    ).replace("<Task>", task_description)
        else:
            return ""

    def query_res(self, info: str):
        return choice(self._responses["query_res"]).replace("<Info>", info)

    def cannot_recognize_entity(self, entity):
        return choice(self._responses["cannot_recognize_entity"]).replace(
            "<Info>", entity
        )

    def confirm_info(self, entity, value, more=False, propose=False):
        if propose:
            return (
                choice(self._responses["confirm_info_with_proposal"])
                .replace("<Info>", entity)
                .replace("<Value>", value)
            )
        elif more:
            return (
                choice(self._responses["confirm_info"])
                .replace("<Info>", entity)
                .replace("<Value>", value + " more")
            )
        else:
            return (
                choice(self._responses["confirm_info"])
                .replace("<Info>", entity)
                .replace("<Value>", value)
            )

    def confirm_retrieved_info(self, entity, value):
        return (
            choice(self._responses["confirm_retrieved_info"])
            .replace("<Info>", entity.replace("_", " "))
            .replace("<Value>", value)
        )

    def ask_spelling(self, spell_type):
        return choice(self._responses["ask_spelling"][spell_type])

    def inform_user(self, entity="", info="None"):
        return (
            choice(self._responses["inform_user"])
            .replace("<Entity>", entity)
            .replace("<Info>", info)
        )

    def verify(self, entity, val, success):
        if success:
            return (
                choice(self._responses["verify_success"])
                .replace("<Info>", entity)
                .replace("<Val>", val)
            )
        else:
            return (
                choice(self._responses["verify_failed"])
                .replace("<Info>", entity)
                .replace("<Val>", val)
            )

    def updated(self, entity="", val=""):
        return (
            choice(self._responses["update_success"])
            .replace("<Info>", entity)
            .replace("<Val>", val)
        )

    def insert(self, info):
        return choice(self._responses["insert"]).replace("<Info>", info)

    def delete(self, info):
        return choice(self._responses["delete"]).replace("<Info>", info)

    def continue_current(self, task):
        return choice(self._responses["continue_current"]).replace("<Task>", task)

    def notify(self):
        return choice(self._responses["notification"])

    def task_finished(self, task):
        res = choice(self._responses["task_finished"]).replace("<Task>", task)
        return res

    def confirm_finish(self):
        return choice(self._responses["confirm_finish"])

    def confirm_satisfied(self):
        return choice(self._responses["confirm_satisfied"])

    def followup(self, task):
        return choice(self._responses["follow_up"]).replace("<Task>", task)

    def welcome_back(self):
        return choice(self._responses["welcome_back"])

    def help_with_prev_task(self, task: str):
        return choice(self._responses["help_with_prev_task"]).replace("<Task>", task)

    def qa(self):
        return choice(self._responses["qa"])

    def api(self, answer: str):
        return choice(self._responses["api"]).replace("<info>", answer)

    def multi_entity(self, cur_entity: str, multiple_entities_pool: list):
        # convert entities into string
        entities = [str(entity) for entity in multiple_entities_pool]

        last_e = entities[-1]
        pool_str = ",".join(entities[:-1]) + " and " + last_e
        return (
            choice(self._responses["multi_entity"])
            .replace("<Entity>", cur_entity)
            .replace("<Pool>", pool_str)
        )

    def suggest_tasks(self, tasks: list):
        """
        Generates a response for when the agent couldn't understand user's intent

        Args:
            tasks: A list of descriptions of tasks (str)
            Return: a response based on the task descriptions
        """
        tasks_des = ""
        for i in range(len(tasks)):
            tasks_des += str(i + 1) + ". " + tasks[i] + "\n"
        return choice(self._responses["suggest_tasks"]).replace("<tasks>", tasks_des)
