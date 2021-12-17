# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from collections import defaultdict
from copy import deepcopy
import logging
import importlib.util

from Converse.entity.entity import (
    extract_value_from_entity,
    extract_display_value_from_entity,
)
from Converse.entity_backend import entity_functions as ef
from Converse.entity.entity_manager import EntityManager
from Converse.config.task_config import TaskConfig, TaskEntity
from Converse.utils.utils import entity_api_call, resp

log = logging.getLogger(__name__)


class DialogState(object):
    def __init__(self):
        """
        Dialogue state object

        Explicitly defining attributes, instead of using a simple dictionary,
        makes it so much easier to track read/write and
        helps IDE trigger warnings
        Attributes of known types should be declared with the expected typing

        Attributes:
            cur_entity_name (str): entity name defined in task and entity
                config files such as email_address, zip_code, user_name, ...
            cur_entity_types (List[str]): a list of entity types, such as EMAIL, PERSON,
                CARDINAL, ...
            last_verified_entity (str): name of the entity that was last updated by
                the tree manager
            last_verified_task (str): name of the task associated with the last verified
                entity
        """
        self.cur_task = None
        self.cur_entity_name = None
        self.cur_entity_types = []

        # if need_confirm_entity is set to true, overrides need_confirm_retrieved_entity
        self.need_confirm_entity: bool = False
        self.need_confirm_retrieved_entity: bool = True
        self.entity_is_retrieved_after_processed_previous_entity: bool = False

        self.confirm_continue: bool = False
        self.task_stack: list = []
        self.exceed_max_turn: bool = False
        self.prev_tasks: list = []
        self.prev_tasks_success: list = []
        self.prev_task_finished: bool = False
        self.prev_task_finish_func_response: str = ""
        self.entity_methods: list = []
        self.spell_entity = None
        self.prev_turn_got_intent = False

        self.new_task = None
        self.confirm_entity: bool = False  # whether agent is expecting user to confirm
        self.unconfirmed_entity_value = None
        self.last_verified_entity = None
        self.last_verified_task = None
        self.last_wrong_entity = None
        self.agent_action_type = None
        self.verify_resp = None
        self.inform_resp = None
        self.api_resp = None
        self.update_resp = None
        self.query_resp = None
        self.simple_resp = None
        self.insert_resp = None
        self.delete_resp = None
        self.task_with_info = None
        self.confirm_intent: bool = False
        self.unconfirmed_intent: list = []
        self.multiple_entities: bool = False
        self.multiple_entities_pool: list = []
        self.polarity = 0

        # states from configuration
        self.max_no_info_turn = 4
        self.continuous_no_info_turn = 0
        self.prev_turn_no_info: bool = False

    def to_dictionary(self) -> dict:
        """
        Export DialogState object to the dictionary format
        """
        return deepcopy(self.__dict__)

    def __eq__(self, other) -> bool:
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    @classmethod
    def from_dictionary(cls, states: dict) -> "DialogState":
        """
        Construct DialogState object by reading from the dictionary format
        """
        dial_states = DialogState()
        for key, val in states.items():
            dial_states.__setattr__(key, val)
        return dial_states


class StatesWithinCurrentTurn:
    def __init__(self):
        """
        Object of dialog states within the current turn,
        will be reset next turn.
        entity_candidates may be changed by new_task_with_info() in dial_policy.py
        """
        # other modules output
        self.extracted_info = dict()
        self.entity_candidates = []
        # states from other modules
        self.asr_out = ""
        self.got_info = False
        self.got_intent = False
        self.got_entity_info = False
        self.got_FAQ = False
        self.got_exact_FAQ = False
        self.got_ner = False
        self.polarity = 0


class StateManager:
    def __init__(
        self,
        entity_manager: EntityManager,
        task_config: TaskConfig,
        entity_function_path=None,
    ):
        self.task_config = task_config
        self.entity_manager = entity_manager
        self.addtional_ef = None
        if entity_function_path:
            spec = importlib.util.spec_from_file_location(
                "additional_entity_function", entity_function_path
            )
            self.addtional_ef = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.addtional_ef)
        self.reset()

    def reset(self):
        self.task_turns = defaultdict(int)
        self.exceed_max_turn_flag = False

    def update_and_get_states(self, ctx):
        """
        Retrieve states from the tree manager, update current states, and return
        current states. This function change the states object in place.
        """
        states = ctx.cur_states
        tree_manager = ctx.tree_manager

        states.cur_task = tree_manager.cur_task
        states.new_task = None
        states.cur_entity_name = tree_manager.cur_entity
        log.info(f"cur_entity_name = {states.cur_entity_name}")
        states.cur_entity_types = self.entity_manager.get_entity_types(
            states.cur_entity_name
        )
        if not (not states.cur_task and states.confirm_continue):
            states.confirm_continue = tree_manager.finish

        if (
            states.cur_task
            and states.cur_entity_name
            and states.cur_task in self.task_config
            and states.cur_entity_name in self.task_config[states.cur_task].entities
        ):
            task_entity_config = self.task_config[states.cur_task].entities[
                states.cur_entity_name
            ]
            states.need_confirm_entity = task_entity_config.confirm

            states.need_confirm_retrieved_entity = task_entity_config.confirm_retrieved
        else:
            states.need_confirm_entity = TaskEntity._OPTIONAL_ATTRIBUTES["confirm"]
            states.need_confirm_retrieved_entity = TaskEntity._OPTIONAL_ATTRIBUTES[
                "confirm_retrieved"
            ]

        states.entity_methods = self.entity_manager.get_extraction_methods(
            states.cur_entity_name
        )
        states.task_stack = tree_manager.task_stack
        states.exceed_max_turn = self.exceed_max_turn_flag
        states.prev_tasks = tree_manager.prev_tasks
        states.prev_tasks_success = tree_manager.prev_tasks_success
        states.prev_task_finished = tree_manager.prev_task_finished

        if states.prev_task_finished or (states.exceed_max_turn and states.prev_tasks):
            self._task_finish_function(ctx)

        self.exceed_max_turn_flag = False
        if states.spell_entity != states.cur_entity_name:
            states.spell_entity = None
        states.agent_action_type = (
            tree_manager.cur_node.tag if tree_manager.cur_node else None
        )

    def _get_entity_or_task_function(self, func_name):
        func = None
        url = None
        if func_name:
            # if the function is in both default ef and additional ef,
            # the one in additional ef will override the one in the default ef
            try:
                func = None
                if self.addtional_ef:
                    func = getattr(self.addtional_ef, func_name, None)
                if not func:
                    func = getattr(ef, func_name)
            except AttributeError:
                url = func_name
        return func, url

    @staticmethod
    def _execute_entity_or_task_function(ctx, func, url):
        try:
            if url:
                res = entity_api_call(
                    url,
                    ctx.collected_entities,
                    **ctx.cur_states.to_dictionary(),
                )
            else:
                res = func(
                    ctx.collected_entities,
                    **ctx.cur_states.to_dictionary(),
                )
        except TimeoutError as e:
            log.warning(f"function call timeout: {e}")
            res = resp(False, "Service time out")
        except Exception as e:  # to catch other issues
            log.warning(f"function call exception: {e}")
            res = resp(False, "We couldn't handle your request")
        return res

    def _task_finish_function(self, ctx):
        """
        The function will check whether there is a task finish
        function and execute if the user specifies one.
        :param ctx: dialog context
        """
        # len(prev_tasks) is equal to len(prev_tasks_success)
        # If sub task is False, prev_tasks is [sub_task, main_task], prev_task_success
        # is [False, False] since main_task requires sub_task to be True
        # In other cases, only one task in prev_tasks
        if ctx.cur_states.prev_tasks_success[0]:
            func_name = self.task_config[
                ctx.cur_states.prev_tasks[0]
            ].task_finish_function
            if func_name:
                # if the function is in both default ef and additional ef,
                # the one in additional ef will override the one in the default ef
                func, url = self._get_entity_or_task_function(func_name)
                res = self._execute_entity_or_task_function(ctx, func, url)
                if not res["success"]:
                    ctx.cur_states.prev_tasks_success[0] = False
                else:
                    ctx.cur_states.prev_task_finish_func_response = res["msg"]

    def receive_info_from_policy(self, ctx):
        """
        receive task and entity information from the policy,
        then update and traverse the task tree.
        """
        # Reset the task turn count after tasks are finished
        states = ctx.cur_states
        tree_manager = ctx.tree_manager
        if tree_manager.prev_tasks:
            for prev_task in tree_manager.prev_tasks:
                self.task_turns[prev_task] = 0
        tree_manager.reset_prev_task()
        if states.cur_task:
            self.task_turns[states.cur_task] += 1
        if states.new_task:
            self.new_task(states.new_task, tree_manager)
        elif ctx.update_entity["entity"]:
            self.leaf_node_handler(ctx)
        if (
            states.cur_task
            and self.task_turns[states.cur_task]
            > self.task_config[states.cur_task].max_turns
        ):
            self.force_cur_task_finish(tree_manager)
            self.exceed_max_turn_flag = True

    def new_task(self, task_name, tree_manager):
        tree_manager.set_task(task_name)
        tree_manager.traverse()

    def leaf_node_handler(self, ctx):
        states = ctx.cur_states
        tree_manager = ctx.tree_manager
        assert tree_manager.cur_task
        assert tree_manager.cur_node
        assert tree_manager.cur_entity
        assert states.agent_action_type
        assert tree_manager.cur_entity == ctx.update_entity["entity"]
        func_name = self.task_config[states.cur_task].entities[states.cur_entity_name][
            "function"
        ]
        func, url = self._get_entity_or_task_function(func_name)
        new_entity_name = ctx.update_entity["entity"]
        new_entity_value = extract_value_from_entity(ctx.update_entity["value"])
        ctx.collected_entities[new_entity_name] = new_entity_value

        log.info(f"collected_entities = {ctx.collected_entities}")
        log.info(f"func_name = {func_name}")
        log.info(f"leaf_node_handler() = {ctx.update_entity}")
        if ctx.update_entity["value"] == "WRONG INFO!":
            states.last_wrong_entity = tree_manager.cur_entity
            states.last_verified_entity = None
            states.last_verified_task = None
            tree_manager.update_entity(
                ctx.update_entity["value"],
                status=False,
            )
            tree_manager.traverse()
        elif states.agent_action_type == tree_manager.task_tree.simple:
            states.simple_resp = extract_display_value_from_entity(
                ctx.update_entity["value"]
            )
            tree_manager.update_entity(
                states.simple_resp,
                status=True,
            )
            tree_manager.traverse()
        else:
            res = self._execute_entity_or_task_function(ctx, func, url)
            states.last_wrong_entity = None
            if states.agent_action_type == tree_manager.task_tree.verify:
                verify_status = res["success"]
                states.verify_resp = res["msg"]
                if verify_status:  # verified
                    tree_manager.update_entity(
                        ctx.update_entity["value"],
                        status=True,
                    )
                    states.last_verified_entity = tree_manager.cur_entity
                    states.last_verified_task = tree_manager.cur_task
                    states.last_wrong_entity = None
                    tree_manager.traverse()
                else:  # not verified
                    states.last_wrong_entity = tree_manager.cur_entity
                    states.last_verified_entity = None
                    states.last_verified_task = None
                    if (
                        not states.spell_entity
                        and "spelling" in states.entity_methods
                        and not ctx.bot_config.text_bot
                    ):
                        states.spell_entity = states.cur_entity_name
                    else:
                        tree_manager.update_entity(
                            ctx.update_entity["value"],
                            status=False,
                        )
                        tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.inform:
                states.inform_resp = res["msg"]
                tree_manager.update_entity(
                    states.inform_resp,
                    status=res["success"],
                )
                tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.update:
                states.update_resp = res["msg"]
                tree_manager.update_entity(
                    states.update_resp,
                    status=res["success"],
                )
                tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.api:
                states.api_resp = res["msg"]
                tree_manager.update_entity(
                    states.api_resp,
                    status=res["success"],
                )
                tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.query:
                states.query_resp = res["msg"]
                tree_manager.update_entity(
                    states.query_resp,
                    status=res["success"],
                )
                tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.insert:
                states.insert_resp = res["msg"]
                tree_manager.update_entity(
                    states.insert_resp,
                    status=res["success"],
                )
                tree_manager.traverse()
            elif states.agent_action_type == tree_manager.task_tree.delete:
                states.delete_resp = res["msg"]
                tree_manager.update_entity(
                    states.delete_resp,
                    status=res["success"],
                )
                tree_manager.traverse()

    def force_cur_task_finish(self, tree_manager):
        tree_manager.force_finish_task()
