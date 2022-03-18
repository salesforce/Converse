# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging
from typing import List

from thefuzz import process

from Converse.dialog_state_manager.dial_state_manager import (
    StateManager,
    StatesWithinCurrentTurn,
)
from Converse.dialog_context.dialog_context import DialogContext
from Converse.entity.entity import ExtractionMethod, Entity, EmailEntity
from Converse.entity.entity_manager import EntityManager
from Converse.response.response import Response
from Converse.config.task_config import TaskConfig, BotConfig
from Converse.utils.utils import get_dict_key
from Converse.utils.yaml_parser import load_dial_logic, load_data

log = logging.getLogger(__name__)


class DialoguePolicy:
    # default parameters, so that `None` can be provided for the default value
    default_response_path = "./Converse/bot_configs/response_template.yaml"
    default_policy_path = "./Converse/bot_configs/policy_config.yaml"
    default_task_path = "./Converse/bot_configs/tasks_yaml/tasks.yaml"
    default_entity_path = "./Converse/bot_configs/entity_config.yaml"
    default_entity_extraction_path = (
        "./Converse/bot_configs/entity_extraction_config.yaml"
    )
    default_info_path = "./Converse/entity_backend/entity_function.py"
    default_entity_function_path = "./Converse/bot_configs/entity_function.py"

    def __init__(
        self,
        response_path: str = None,
        policy_path: str = None,
        task_path: str = None,
        entity_path: str = None,
        entity_extraction_path: str = None,
        entity_function_path: str = None,
    ):
        self.task_path = task_path or self.default_task_path
        self.policy_path = policy_path or self.default_policy_path
        self.entity_path = entity_path or self.default_entity_path
        self.entity_extraction_path = (
            entity_extraction_path or self.default_entity_extraction_path
        )
        self.response_path = response_path or self.default_response_path
        self.entity_function_path = (
            entity_function_path or self.default_entity_function_path
        )
        self.entity_manager = EntityManager(
            self.entity_path, self.entity_extraction_path
        )
        self.task_config = TaskConfig(self.task_path)
        self.bot_config = BotConfig(self.task_path)
        self.state_manager = StateManager(
            entity_manager=self.entity_manager,
            task_config=self.task_config,
            entity_function_path=self.entity_function_path,
        )
        self.reset()

    def reset(self):
        self.policy = load_dial_logic(self.policy_path)
        self.policy_flags = load_data(self.policy_path, "Flag")
        self.policy_states = load_data(self.policy_path, "State")
        self.bot_config = BotConfig(self.task_path)
        self.response = Response(
            template=self.response_path,
            task_config=self.task_config,
            bot_config=self.bot_config,
            entity_manager=self.entity_manager,
        )

        self.state_manager.reset()

    def policy_tree(
        self,
        data: dict,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
    ) -> str:
        """Take dialog management actions

        Based on the policy config, NLU models results, dialog context and
        dialog states within current turn.

        Return the response(str).

        Attributes:
            data(dict): policy configuration
            ctx(DialogContext): dialog states between turns
             (will possibly be modified in place)
            cur_turn_states(StatesWithenCurrentTurn): dialog states within current turn
        """
        for node in data:
            if isinstance(node, dict):  # dialogue states
                op = get_dict_key(node)
                if op in ctx.policy_map:
                    ops = ctx.policy_map[op]
                else:
                    ops = op.split()
                    for i in range(len(ops)):
                        if ops[i] in self.policy_flags:
                            ops[i] = "cur_turn_states." + ops[i]
                        elif ops[i] in self.policy_states:
                            ops[i] = "ctx.cur_states." + ops[i]
                    ops = " ".join(ops)
                    ctx.policy_map[op] = ops
                if eval(ops):
                    log.info("%s is True", ops)
                    res = self.policy_tree(
                        node[op], ctx=ctx, cur_turn_states=cur_turn_states
                    )  # dfs
                    if res:
                        return res
                else:
                    log.info("%s is False", ops)

            elif isinstance(node, str):  # dialogue actions
                if node != "PASS":
                    log.info("executing %s", node)
                    res = eval(
                        "self." + node + "(ctx=ctx, cur_turn_states=cur_turn_states)"
                    )
                    if res:
                        return res

    def _set_state_for_confirm_task(
        self, task, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ):
        """
        Set internal state variables to prepare for asking the user to confirm
        the task in the next turn.

        :param task: the name of the task to confirm (str)
        """
        cur_turn_states.got_intent = False
        ctx.cur_states.confirm_intent = True
        ctx.cur_states.unconfirmed_intent.append(task)

    def ask_confirm_task(
        self, task, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ):
        """
        Set the internal state and generate the response to ask the user to
        confirm the given task in the next turn.

        :param task: the name of the task to confirm (str)
        :return: the response to ask the user to confirm the task (str)
        """
        self._set_state_for_confirm_task(task, ctx, cur_turn_states)
        response = self.response.confirm_intent(self.task_config[task].description)
        return response

    def got_new_task(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn, model=False
    ) -> str:
        if not model:
            response_tmp = self._set_task(ctx)
            if ctx.cur_states.agent_action_type != "INFORM":
                if not ctx.repeat:
                    candidates = self._get_entity_candidates_from_history(ctx)
                    if candidates:
                        response_tmp += " " + self.entity_info_handler(
                            ctx, cur_turn_states, candidates=candidates
                        )
                    else:
                        response_tmp += " " + self.response.ask_info(
                            ctx.cur_states.cur_task,
                            ctx.cur_states.cur_entity_name,
                        )
                else:
                    response_tmp += " " + self.response.ask_info(
                        ctx.cur_states.cur_task,
                        ctx.cur_states.cur_entity_name,
                    )
            else:  # inform
                response_tmp = self._inform_user(ctx, cur_turn_states)
                ctx.reset_update()
            return response_tmp

    def new_task_with_info(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn, model=False
    ) -> str:
        if not model:
            main_task = ctx.cur_states.new_task
            response_tmp = self._set_task(ctx)

            # find out methods to extract entities
            methods = self.entity_manager.get_extraction_methods(
                ctx.cur_states.cur_entity_name,
            )

            entity_classes = self.entity_manager.get_entity_classes(
                ctx.cur_states.cur_entity_name,
            )

            if cur_turn_states.got_ner and (
                "USER_UTT" in ctx.cur_states.cur_entity_types
                or "PICKLIST" in ctx.cur_states.cur_entity_types
            ):
                """
                Sometimes, this dialogue action is triggered by intent plus NER info
                when the intent doesn't actually need NER info. For "USER_UTT"
                and "PICKLIST" entities, we want to skip entity extraction here.
                """
                entity_candidates = []
            else:
                # extract entities again now that we have updated the methods
                entity_candidates = self.entity_manager.extract_entities(
                    utterance=ctx.user_response,
                    methods=methods,
                    ner_model_output=cur_turn_states.extracted_info["ner"],
                    entity_types=entity_classes,
                )

            for entity in entity_candidates:
                ctx.entity_history_manager.insert(entity, ctx.turn)

            # filter extracted entity by its type
            cur_turn_states.entity_candidates = entity_candidates = [
                entity for entity in entity_candidates if type(entity) in entity_classes
            ]

            if not ctx.repeat:
                history_candidates = self._get_entity_candidates_from_history(ctx)
                entity_candidates.extend(history_candidates)
            if ctx.cur_states.cur_task == main_task:  # no sub_task
                entity_response = self.entity_info_handler(
                    ctx, cur_turn_states, entity_candidates
                )
                if entity_response:
                    response_tmp += " " + entity_response
                elif ctx.cur_states.agent_action_type != "INFORM":
                    response_tmp += " " + self.response.ask_info(
                        ctx.cur_states.cur_task,
                        ctx.cur_states.cur_entity_name,
                    )
                else:  # inform
                    response_tmp = self._inform_user(ctx, cur_turn_states)
                    ctx.reset_update()
            else:
                ctx.cur_states.task_with_info = (
                    main_task,
                    len(ctx.user_history.user_utt_norm) - 1,
                )
                self.state_manager.receive_info_from_policy(ctx)
                if ctx.cur_states.agent_action_type != "INFORM":
                    if not entity_candidates:
                        response_tmp += " " + self.response.ask_info(
                            ctx.cur_states.cur_task,
                            ctx.cur_states.cur_entity_name,
                        )
                    else:
                        response_tmp += " " + self.entity_info_handler(
                            ctx, cur_turn_states, candidates=entity_candidates
                        )
                else:  # inform
                    response_tmp = self._inform_user(ctx, cur_turn_states)
                    ctx.reset_update()
            return response_tmp

    def _set_task(self, ctx: DialogContext) -> str:
        # send info to state manager
        ctx.cur_states.confirm_intent = False
        ctx.cur_states.unconfirmed_intent = []
        self.state_manager.receive_info_from_policy(ctx)
        # generate response
        main_task = ctx.cur_states.new_task
        if not ctx.cur_states.cur_task:
            response_tmp = self.response.got_intent(
                self.task_config[ctx.cur_states.new_task].description
            )
        else:
            response_tmp = self.response.got_intent(
                self.task_config[ctx.cur_states.new_task].description,
                first=False,
            )
        # entity and sub_task
        self.state_manager.update_and_get_states(ctx)
        assert ctx.cur_states.cur_task
        assert ctx.cur_states.cur_entity_name
        if ctx.cur_states.cur_task != main_task:  # sub_task
            response_tmp += " " + self.response.got_sub_task(
                self.task_config[ctx.cur_states.cur_task].description
            )
        return response_tmp

    def task_confirm_handler(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn, model=False
    ) -> str:
        """
        Handles the unconfirmed intent.
        If the user confirms, then set new task,
        else abandon the unconfirmed intent.

        Note that there could be 2 unconfirmed intents at one time,
        this happens when the user refuses to confirm a repeatable task,
        and brings up a new uncertain intent.
        In this scenario, if the user then confirm the new uncertain intent,
        the task_confirm_handler will be called twice,
        the repeatable task will be abandoned;
        else the repeatable task and the new uncertain intent will both be abandoned
        """
        if not model:
            if cur_turn_states.polarity == 1:  # confirmed the unconfirmed task
                ctx.cur_states.new_task = ctx.cur_states.unconfirmed_intent.pop()
                if ctx.cur_states.unconfirmed_intent:
                    cur_turn_states.polarity = 0
                    cur_turn_states.got_intent = ctx.cur_states.prev_turn_got_intent
                    return self.task_confirm_handler(ctx, cur_turn_states)
                else:
                    if cur_turn_states.got_entity_info:
                        return self.new_task_with_info(ctx, cur_turn_states)
                    return self.got_new_task(ctx, cur_turn_states)
            else:  # refused the unconfirmed task
                if len(ctx.cur_states.unconfirmed_intent) >= 2:
                    ctx.cur_states.unconfirmed_intent.pop()
                if ctx.repeat:
                    ctx.repeat = False
                if cur_turn_states.got_intent:
                    if cur_turn_states.got_entity_info:
                        return self.new_task_with_info(ctx, cur_turn_states)
                    return self.got_new_task(ctx, cur_turn_states)
                else:
                    ctx.cur_states.confirm_intent = False
                    ctx.cur_states.unconfirmed_intent.pop()
                    if ctx.cur_states.cur_task and ctx.cur_states.cur_entity_name:
                        if ctx.cur_states.agent_action_type != "INFORM":
                            response_tmp = self.response.ask_info(
                                ctx.cur_states.cur_task,
                                ctx.cur_states.cur_entity_name,
                            )
                        else:  # inform
                            response_tmp = self._inform_user(ctx, cur_turn_states)
                        ctx.reset_update()
                        return response_tmp
                    else:
                        ctx.cur_states.confirm_continue = True
                        return self.response.confirm_finish()

    def entity_info_handler(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        candidates: List[Entity] = None,
    ) -> str:
        """
        if candidates are not explicitly provided,
        it will use self.entity_candidates
        """
        candidate_list = candidates if candidates else cur_turn_states.entity_candidates

        # filter the candidate by the expected type
        entity_classes = self.entity_manager.get_entity_classes(
            ctx.cur_states.cur_entity_name,
        )

        if not entity_classes:
            candidate_list = []
        else:
            candidate_list = [
                candidate
                for candidate in candidate_list
                if type(candidate) in entity_classes
            ]

        # check whether an entity extracted from the spelling is present
        spelling_entity = False
        for candidate in candidate_list:
            if candidate.method == ExtractionMethod.SPELLING:
                spelling_entity = True
                break

        # extract unique entity values as a list
        # we want to keep the entity type, so `candidate_list` is a list of entity
        # instances, rather than entity values
        candidate_list = Entity.unique(candidate_list)

        response_tmp = ""

        if ctx.cur_states.multiple_entities:
            got_entity, entity = self.choose_entity(ctx, cur_turn_states)
            ctx.cur_states.multiple_entities = False
            ctx.cur_states.multiple_entities_pool = []
            if got_entity:
                ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
                ctx.update_entity["value"] = entity
                ctx.update_entity["task"] = ctx.cur_states.cur_task
                response_tmp = self._check_info(ctx, cur_turn_states)
                return response_tmp
            else:
                response_tmp = self.response.ask_info(
                    ctx.cur_states.cur_task,
                    ctx.cur_states.cur_entity_name,
                )
                return response_tmp

        log.info(f"cur_task = {ctx.cur_states.cur_task}")
        log.info(f"spelling_entity = {spelling_entity}")
        log.info("need_confirm_entity = " f"{ctx.cur_states.need_confirm_entity}")

        # save current entity name before it is overwritten
        entity_name = ctx.cur_states.cur_entity_name
        # current task's config before it's written by the new task
        if ctx.cur_states.cur_task:
            task_config = self.task_config[ctx.cur_states.cur_task]
        else:
            task_config = None

        if not candidate_list:
            return response_tmp  # no valid entity.

        elif len(candidate_list) == 1:
            entity = candidate_list[0]

            # confirm the entity if confirm is set (overrides retrieved)
            # or the entity is a retrieved entity and confirm_retrieved is set
            retrieved_entity = (
                ctx.cur_states.need_confirm_retrieved_entity
                and self._is_retrieved_entity(ctx, entity)
            )
            need_confirm_entity = ctx.cur_states.need_confirm_entity or retrieved_entity

            if (
                spelling_entity and not self.bot_config.text_bot
            ):  # single spelling entity
                if need_confirm_entity:
                    response_tmp = self._ask_confirm(
                        ctx.cur_states.cur_entity_name,
                        entity,
                        ctx,
                        retrieved=retrieved_entity,
                    )
                    self.state_manager.receive_info_from_policy(ctx)
                    log.info("confirm_entity = " f"{ctx.cur_states.confirm_entity}")
                    log.info("cur_entity_name = " f"{ctx.cur_states.cur_entity_name}")
                else:
                    ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
                    ctx.update_entity["value"] = entity
                    ctx.update_entity["task"] = ctx.cur_states.cur_task
                    response_tmp = self._check_info(ctx, cur_turn_states)

            else:  # single non-spelling entity
                if not need_confirm_entity:
                    ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
                    ctx.update_entity["value"] = entity
                    ctx.update_entity["task"] = ctx.cur_states.cur_task
                    response_tmp = self._check_info(ctx, cur_turn_states)
                else:
                    ctx.reset_update()
                    response_tmp = self._ask_confirm(
                        ctx.cur_states.cur_entity_name,
                        entity,
                        ctx,
                        retrieved=retrieved_entity,
                    )
                    self.state_manager.receive_info_from_policy(ctx)

        else:  # multiple entity types
            ctx.cur_states.multiple_entities = True
            ctx.cur_states.multiple_entities_pool = candidate_list
            response_tmp = self.response.multi_entity(
                ctx.cur_states.cur_entity_name,
                [
                    entity.display_value()
                    for entity in ctx.cur_states.multiple_entities_pool
                ],
            )

        if task_config and task_config.entities[entity_name].forget:
            # if 'forget' not defined explicitly, it is assumed to be false by default
            ctx.entity_history_manager.remove_named_entity(entity_name)
            for entity in candidate_list:
                ctx.entity_history_manager.remove(entity)
        return response_tmp

    def choose_entity(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        threshold=90,
    ):
        """
        choose entity from an entity pool based on cur_turn_states.asr_out and
        cur_turn_states.extracted_info,
        return got_entity:bool and entity:Entity
        """

        def ordinal(info):
            order = None
            # TODO: this is too hacky, may need a better way in the future
            ordinal_dict = {
                "latter": -1,
                "former": 0,
                "middle": 1,
                "last": -1,
                "first": 0,
                "second": 1,
                "third": 2,
            }
            for key in ordinal_dict:
                if key in cur_turn_states.asr_out:
                    order = ordinal_dict[key]
            ner_spans = (
                info["ner"]["probabilities"] if "probabilities" in info["ner"] else []
            )
            for name_entity in ner_spans:
                if (
                    name_entity["label"] == "ORDINAL"
                    and name_entity["token"] in ordinal_dict
                ):
                    order = ordinal_dict[name_entity["token"]]
            return order

        got_entity, entity = False, None
        info = cur_turn_states.extracted_info
        entities_pool = ctx.cur_states.multiple_entities_pool
        wordlist = info["negation"]["wordlist"]
        if info["negation"]["triplets"][0] != (-1, -1, -1):
            for negation in info["negation"]["triplets"]:
                scope = " ".join(wordlist[negation[1] : negation[2]])
                fuzzy_entity, fuzzy_score, fuzzy_index = process.extractOne(
                    scope,
                    dict(
                        map(lambda x: (x[0], str(x[1].value)), enumerate(entities_pool))
                    ),
                )
                if fuzzy_score >= threshold:
                    entities_pool.pop(fuzzy_index)
            if len(entities_pool) == 1:
                got_entity, entity = True, entities_pool[0]
        else:
            order = ordinal(info)
            if order is not None:
                got_entity, entity = (
                    True,
                    ctx.cur_states.multiple_entities_pool[order],
                )
            else:
                entity_value_candidates = [str(x.value) for x in entities_pool]
                if cur_turn_states.asr_out in entity_value_candidates:  # exact match
                    got_entity, entity = True, cur_turn_states.asr_out
                else:
                    fuzzy_entity, fuzzy_score, fuzzy_index = process.extractOne(
                        cur_turn_states.asr_out,
                        dict(
                            map(
                                lambda x: (x[0], str(x[1].value)),
                                enumerate(entities_pool),
                            )
                        ),
                    )
                    if fuzzy_score >= threshold:
                        got_entity, entity = True, entities_pool[fuzzy_index]

        log.info("choose_entity %s %s", got_entity, entity)
        return got_entity, entity

    def _repeat_task(
        self, task, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        """
        Set the internal state to prepare for task confirmation and generate a
        response to ask the user if they would like to repeat the given task.

        :param task: Name of the task to repeat (str)
        :return: the response to ask the user if they would like to repeat the
        task (str)
        """
        self._set_state_for_confirm_task(task, ctx, cur_turn_states)
        response_tmp = self.response.task_repeat_response(task)
        ctx.repeat = True
        return response_tmp

    def _inform_user(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        ctx.reset_update()
        ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
        ctx.update_entity["task"] = ctx.cur_states.cur_task
        cur_task = ctx.cur_states.cur_task
        self.state_manager.receive_info_from_policy(ctx)
        self.state_manager.update_and_get_states(ctx)
        assert ctx.cur_states.inform_resp
        response_tmp = self.response.entity_response(
            task=cur_task,
            entity=ctx.update_entity["entity"],
            info=ctx.cur_states.inform_resp,
        )
        if not response_tmp:
            response_tmp = self.response.inform_user(
                ctx.update_entity["entity"], ctx.cur_states.inform_resp
            )
        if ctx.cur_states.prev_task_finished:
            prev_task_finished_response = self.response.task_finish_response(
                ctx.cur_states.prev_tasks,
                ctx.cur_states.prev_tasks_success,
                ctx.cur_states.prev_task_finish_func_response,
            )
            ctx.cur_states.prev_task_finish_func_response = ""
            if prev_task_finished_response:
                response_tmp += " " + prev_task_finished_response
        if ctx.cur_states.prev_task_finished and self.task_config[cur_task].repeat:
            response_tmp += " " + self._repeat_task(cur_task, ctx, cur_turn_states)
        elif ctx.cur_states.confirm_continue:
            response_tmp += " " + self.response.confirm_finish()
        elif ctx.cur_states.agent_action_type == "INFORM":
            response_tmp += " " + self._inform_user(ctx, cur_turn_states)
        elif ctx.cur_states.agent_action_type and ctx.cur_states.cur_entity_name:
            response_tmp += " " + self.response.ask_info(
                ctx.cur_states.cur_task,
                ctx.cur_states.cur_entity_name,
            )
        ctx.reset_update()
        ctx.cur_states.inform_resp = None
        return response_tmp

    def _ask_confirm(
        self, entity_name, entity, ctx: DialogContext, retrieved=False
    ) -> str:
        """Get info, ask for confirmation"""
        if isinstance(entity, EmailEntity) and not self.bot_config.text_bot:
            return self._confirm_email(entity, ctx)

        ctx.cur_states.confirm_entity = True
        ctx.cur_states.unconfirmed_entity_value = entity
        if retrieved:
            return self.response.confirm_retrieved_info(
                entity_name, entity.display_value()
            )
        return self.response.confirm_info(entity_name, entity.display_value())

    def _confirm_email(self, email_entity, ctx: DialogContext) -> str:
        email = str(email_entity.value)
        ctx.cur_states.unconfirmed_entity_value = email_entity
        email_split = email.split("@")
        confirm_info = (
            " ".join(list(email_split[0].upper()))
            + " at "
            + email_split[1].replace(".", " dot ")
        )
        ctx.cur_states.confirm_entity = True
        return self.response.confirm_info(ctx.cur_states.cur_entity_name, confirm_info)

    def _check_info(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        cur_task = ctx.cur_states.cur_task
        log.info(f"cur_task = {cur_task}")
        self.state_manager.receive_info_from_policy(ctx)
        self.state_manager.update_and_get_states(ctx)
        if ctx.cur_states.exceed_max_turn and not ctx.cur_states.cur_task:
            log.info("(exceed_max_turn and not cur_task) is True")
            return self.response.forward_to_human()
        elif ctx.cur_states.exceed_max_turn and ctx.cur_states.prev_tasks:
            log.info("(exceed_max_turn and prev_tasks) is True")
            prev_res = self.response.task_finish_response(
                ctx.cur_states.prev_tasks,
                ctx.cur_states.prev_tasks_success,
                ctx.cur_states.prev_task_finish_func_response,
            )
            ctx.cur_states.prev_task_finish_func_response = ""
            res = prev_res + " " + self.response.forward_to_human()
            return res.strip()
        if ctx.cur_states.task_with_info and (
            ctx.cur_states.task_with_info[0] == ctx.cur_states.cur_task
        ):
            log.info("(task_with_info and task_with_info[0] == cur_task) is True")
            if ctx.cur_states.agent_action_type != "INFORM":
                entity_type = ctx.cur_states.cur_entity_types[0]
                ctx.reset_update()
                candidates = []
                if candidates:
                    return self.entity_info_handler(ctx, cur_turn_states, candidates)
            else:
                ctx.reset_update()
                return self._inform_user(ctx, cur_turn_states)
        if (
            ctx.cur_states.last_verified_entity and not ctx.cur_states.last_wrong_entity
        ):  # verified
            log.info("last_verified_entity is True")
            log.info(
                (
                    "ctx.cur_states.cur_entity_name = "
                    f"{ctx.cur_states.cur_entity_name}"
                )
            )
            log.info("agent_action_type = " f"{ctx.cur_states.agent_action_type}")
            response_tmp = ""
            if ctx.cur_states.verify_resp:
                response_tmp = self.response.entity_response(
                    task=ctx.update_entity["task"],
                    entity=ctx.cur_states.last_verified_entity,
                    info=ctx.cur_states.verify_resp,
                )
                ctx.cur_states.verify_resp = None
            if not response_tmp:
                response_tmp = self.response.okay()
            if ctx.cur_states.prev_task_finished:  # previous task can be finished
                prev_task_finished_response = self.response.task_finish_response(
                    ctx.cur_states.prev_tasks,
                    ctx.cur_states.prev_tasks_success,
                    ctx.cur_states.prev_task_finish_func_response,
                )
                ctx.cur_states.prev_task_finish_func_response = ""
                if prev_task_finished_response:
                    response_tmp += " " + prev_task_finished_response
            if ctx.update_entity["entity"] != ctx.cur_states.cur_entity_name:
                ctx.reset_update()
                if ctx.cur_states.agent_action_type != "INFORM":
                    candidates = self._get_entity_candidates_from_history(ctx)
                    log.info(f"candidates = {candidates}")
                    if candidates:
                        ctx.cur_states.entity_is_retrieved_after_processed_previous_entity = (
                            True
                        )
                        response_tmp += " " + self.entity_info_handler(
                            ctx, cur_turn_states, candidates=candidates
                        )
                    else:
                        response_tmp += " " + self.response.ask_info(
                            ctx.cur_states.cur_task,
                            ctx.cur_states.cur_entity_name,
                        )
                else:  # inform
                    response_tmp += " " + self._inform_user(ctx, cur_turn_states)
            ctx.cur_states.last_verified_entity = None
            ctx.cur_states.last_verified_task = None
            ctx.cur_states.last_wrong_entity = None
        elif (
            ctx.cur_states.last_wrong_entity
            and ctx.cur_states.last_wrong_entity == ctx.update_entity["entity"]
        ):  # verify failed
            log.info(
                "(last_wrong_entity and last_wrong_entity == "
                "update_entity['entity']) is True"
            )
            if (
                ctx.cur_states.cur_entity_name
                and ctx.cur_states.spell_entity == ctx.cur_states.cur_entity_name
                and not self.bot_config.text_bot
            ):
                # ask for spelling
                # will ask for the first entity type only if there are multiple
                response_tmp = self.response.ask_spelling(
                    ctx.cur_states.cur_entity_types[0]
                )
            else:
                response_tmp = ""
                if ctx.cur_states.verify_resp:
                    response_tmp = self.response.entity_response(
                        task=ctx.update_entity["task"],
                        entity=ctx.cur_states.last_verified_entity,
                        info=ctx.cur_states.verify_resp,
                    )
                    ctx.cur_states.verify_resp = None
                if not response_tmp:
                    response_tmp = self._cannot_recognize_entity(ctx, cur_turn_states)
        else:  # not verification
            log.info("executing _responses_not_verify_or_inform()")
            response_tmp = self._responses_not_verify_or_inform(
                ctx.update_entity["task"], ctx, cur_turn_states
            )
        ctx.reset_update()
        return response_tmp

    def fail_entity(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
        ctx.update_entity["value"] = "WRONG INFO!"
        ctx.update_entity["task"] = ctx.cur_states.cur_task
        self.state_manager.receive_info_from_policy(ctx)

        self.state_manager.update_and_get_states(ctx)
        if ctx.cur_states.last_wrong_entity and (
            ctx.cur_states.last_wrong_entity == ctx.update_entity["entity"]
        ):  # verify failed
            response_tmp = self._cannot_recognize_entity(ctx, cur_turn_states)
        else:  # not verification
            response_tmp = self._responses_not_verify_or_inform(
                ctx.update_entity["task"], ctx, cur_turn_states
            )
        ctx.reset_update()
        return response_tmp

    def _cannot_recognize_entity(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ):
        """Generates a response when the last entity cannot be recognized."""
        response_tmp = self.response.cannot_recognize_entity(
            ctx.cur_states.last_wrong_entity
        )
        if not ctx.cur_states.cur_task:  # task failed
            response_tmp += " " + self.response.forward_to_human()
            ctx.finish_and_fail = True
        else:
            if ctx.cur_states.cur_entity_name != ctx.cur_states.last_wrong_entity:
                candidates = self._get_entity_candidates_from_history(ctx)
                if candidates:
                    response_tmp += " " + self.entity_info_handler(
                        ctx, cur_turn_states, candidates=candidates
                    )
                else:
                    response_tmp += " " + self.response.ask_info(
                        ctx.cur_states.cur_task,
                        ctx.cur_states.cur_entity_name,
                    )
            else:
                response_tmp += " " + self.response.ask_info(
                    ctx.cur_states.cur_task,
                    ctx.cur_states.cur_entity_name,
                )
        return response_tmp

    def _responses_not_verify_or_inform(
        self, task, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        """
        :param task: current task name
        :param ctx: dialogue context
        :param cur_turn_states: dialogue states within current turn
        :return: generated response when entity type is not VERIFY or INFORM
        """
        if ctx.cur_states.simple_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.simple_resp,
            )
            ctx.cur_states.simple_resp = None
        elif ctx.cur_states.update_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.update_resp,
            )
            if not response_tmp:
                response_tmp = self.response.updated()
            ctx.cur_states.update_resp = None
        elif ctx.cur_states.query_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.query_resp,
            )
            if not response_tmp:
                response_tmp = self.response.query_res(ctx.cur_states.query_resp)
            ctx.cur_states.query_resp = None
        elif ctx.cur_states.api_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.api_resp,
            )
            if not response_tmp:
                response_tmp = self.response.api(ctx.cur_states.api_resp)
            ctx.cur_states.api_resp = None
        elif ctx.cur_states.insert_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.insert_resp,
            )
            if not response_tmp:
                response_tmp = self.response.insert(ctx.cur_states.insert_resp)
            ctx.cur_states.insert_resp = None
        elif ctx.cur_states.delete_resp:
            response_tmp = self.response.entity_response(
                task=task,
                entity=ctx.update_entity["entity"],
                info=ctx.cur_states.delete_resp,
            )
            if not response_tmp:
                response_tmp = self.response.delete(ctx.cur_states.delete_resp)
            ctx.cur_states.delete_resp = None
        else:  # TODO: other leaf node types
            response_tmp = self.empty_response(ctx, cur_turn_states)
        if ctx.cur_states.prev_task_finished:
            prev_task_finished_response = self.response.task_finish_response(
                ctx.cur_states.prev_tasks,
                ctx.cur_states.prev_tasks_success,
                ctx.cur_states.prev_task_finish_func_response,
            )
            ctx.cur_states.prev_task_finish_func_response = ""
            if prev_task_finished_response:
                response_tmp += " " + prev_task_finished_response
        if ctx.cur_states.prev_task_finished and self.task_config[task].repeat:
            response_tmp += " " + self._repeat_task(task, ctx, cur_turn_states)
        elif ctx.cur_states.confirm_continue:
            response_tmp += " " + self.response.confirm_finish()
        elif ctx.cur_states.cur_task and ctx.cur_states.cur_entity_name:
            if ctx.cur_states.agent_action_type != "INFORM":
                candidates = self._get_entity_candidates_from_history(ctx)
                log.info(f"candidates = {candidates}")
                if candidates:
                    ctx.cur_states.entity_is_retrieved_after_processed_previous_entity = (
                        True
                    )
                    response_tmp += " " + self.entity_info_handler(
                        ctx, cur_turn_states, candidates=candidates
                    )
                else:
                    response_tmp += " " + self.response.ask_info(
                        ctx.cur_states.cur_task,
                        ctx.cur_states.cur_entity_name,
                    )
            else:  # inform
                response_tmp += " " + self._inform_user(ctx, cur_turn_states)
        return response_tmp

    def _get_entity_candidates_from_history(self, ctx: DialogContext) -> List[Entity]:
        """
        retrieve entities matching current entity type from the history from
        all turns and all methods, filtered by current task's retrieval config
        specified in task yaml's entities dictionary with the key "retrieve"
        """
        cur_task = ctx.cur_states.cur_task
        cur_entity_name = ctx.cur_states.cur_entity_name
        cur_task_entity_config = self.task_config[cur_task].entities[cur_entity_name]
        # we assume that "retrieve" config is true by default

        if cur_task_entity_config.retrieve:
            turns = None  # default means retrieve from all turns
            entity_classes = self.entity_manager.get_entity_classes(
                ctx.cur_states.cur_entity_name,
            )
            entities = []
            for entity_class in entity_classes:
                entities.extend(
                    ctx.entity_history_manager.retrieve(
                        entity_class,
                        entity_name=ctx.cur_states.cur_entity_name,
                        turns=turns,
                    )
                )
        else:
            # we do not want to retrieve entities from history
            entities = []

        return entities

    def entity_confirm_handler(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ) -> str:
        log.info(f"polarity = {cur_turn_states.polarity}")
        log.info(f"cur_entity_name = {ctx.cur_states.cur_entity_name}")
        ctx.cur_states.confirm_entity = False
        if cur_turn_states.polarity == 1:
            ctx.update_entity["entity"] = ctx.cur_states.cur_entity_name
            ctx.update_entity["value"] = ctx.cur_states.unconfirmed_entity_value
            ctx.entity_history_manager.insert_named_entity(
                ctx.cur_states.cur_entity_name,
                ctx.cur_states.unconfirmed_entity_value,
            )
            ctx.update_entity["task"] = ctx.cur_states.cur_task
            response_tmp = self._check_info(ctx, cur_turn_states)
            ctx.cur_states.unconfirmed_entity_value = None
        else:  # confirm wrong/ no confirmation, get more info
            if not cur_turn_states.got_entity_info:
                if ctx.cur_states.cur_entity_name:
                    if ctx.cur_states.agent_action_type != "INFORM":
                        response_tmp = self.response.ask_info(
                            ctx.cur_states.cur_task,
                            ctx.cur_states.cur_entity_name,
                        )
                    else:  # inform
                        response_tmp = self._inform_user(ctx, cur_turn_states)
                        ctx.reset_update()
                elif not ctx.cur_states.cur_task:
                    response_tmp = " " + self.response.forward_to_human()
                    ctx.finish_and_fail = True
                else:
                    response_tmp = self.response.cannot_recognize_entity(
                        ctx.cur_states.last_wrong_entity
                    )
                ctx.cur_states.unconfirmed_entity_value = None
            else:
                response_tmp = self.entity_info_handler(ctx, cur_turn_states)
        return response_tmp

    def _is_retrieved_entity(self, ctx: DialogContext, entity: Entity) -> bool:
        """
        If the entity is retrieved from the past turn, it is a retrieved entity
        If entity's turn is not present, return false.
        The entity can also be retrieved from the same turn if the bot just
        processed a previous entity.
        """
        if not ctx.cur_states.entity_is_retrieved_after_processed_previous_entity:
            return entity.turn < ctx.turn if entity.turn else False
        else:
            ctx.cur_states.entity_is_retrieved_after_processed_previous_entity = False
            return entity.turn <= ctx.turn if entity.turn else False

    def empty_response(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        model=False,
        **kwargs,
    ) -> str:
        """
        This action is triggered usually when the bot cannot get
        useful information from user. It can return empty response
        when the bot is currently paused, or return confirm finish
        when FAQ is finished and no current task, or repeat the
        previous response in the other cases.
        """
        ctx.cur_states.confirm_continue = False

        ctx.reset_update()
        self.state_manager.receive_info_from_policy(ctx)

        if not model:
            if ctx.do_pause:
                return "<empty></empty>"
            # the current turn is answering a question
            # and there's no other task on the task tree
            if cur_turn_states.got_FAQ or cur_turn_states.got_exact_FAQ:
                if not ctx.cur_states.cur_task:
                    ctx.cur_states.confirm_continue = True
                    return self.response.confirm_finish()
            if ctx.last_response:
                log.debug("Got no information. Repeat last response.")
                return ctx.last_response
            return self.suggest_tasks()

    def no_entity_candidate_selected(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        model=False,
        **kwargs,
    ) -> str:
        """
        In the previous turn, the bot provided multiple entity candidates,
        and let user to choose one from them. If the user says something
        negative, like "None of them", this action will be triggered.
        """
        if not model:
            ctx.cur_states.multiple_entities = False
            ctx.cur_states.multiple_entities_pool = []
            ctx.cur_states.entity_is_retrieved_after_processed_previous_entity = False
            response_tmp = self.response.ask_info(
                ctx.cur_states.cur_task,
                ctx.cur_states.cur_entity_name,
            )
            return response_tmp

    def suggest_tasks(self, model=False, **kwargs) -> str:
        """
        This action can tell users what the bot is capable of
        when it cannot get clear intent from user.
        """
        if not model:
            return self.response.suggest_tasks(self.task_config.get_descriptions())

    def forward_to_human(self, **kwargs) -> str:
        """
        This action will respond forward to human when it is not
        able to handle the current task.
        """
        return self.response.forward_to_human()

    def greetings(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        model=False,
        **kwargs,
    ) -> str:
        """
        This action will send greeting response to user.
        """
        if not model:
            return self.response.greeting()

    def goodbye(
        self,
        ctx: DialogContext,
        cur_turn_states: StatesWithinCurrentTurn,
        model=False,
        **kwargs,
    ) -> str:
        """
        This action will send goodbye response to user.
        """
        ctx.cur_states.confirm_continue = False

        self.state_manager.receive_info_from_policy(ctx)

        if not model:
            return self.response.goodbye()

    def welcome_back(self, ctx: DialogContext, model=False, **kwargs) -> str:
        """
        This action happens when the conversation was paused and then the user
        says something like 'I am back'.
        """
        if not model:
            ctx.last_response = self.response.welcome_back()
            return ctx.last_response
