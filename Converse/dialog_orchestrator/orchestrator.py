# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging

from fuzzysearch import find_near_matches
from thefuzz import fuzz, process
from random import choice

from Converse.dialog_info_layer.dial_info import InfoManager
from Converse.dialog_policy.dial_policy import DialoguePolicy
from Converse.entity.entity_manager import EntityManager
from Converse.dialog_state_manager.dial_state_manager import StatesWithinCurrentTurn

from Converse.utils.yaml_parser import load_dial_logic
from Converse.dialog_context.dialog_context import DialogContext
from Converse.config.task_config import TaskConfig, FAQConfig

log = logging.getLogger(__name__)


class Orchestrator:
    # default parameters, so that `None` can be provided for the default value
    default_response_path = "./Converse/bot_configs/response_template.yaml"
    default_policy_path = "./Converse/bot_configs/policy_config.yaml"
    default_task_path = "./Converse/bot_configs/online_shopping/tasks.yaml"
    default_entity_path = "./Converse/bot_configs/online_shopping/entity_config.yaml"
    default_entity_extraction_path = (
        "./Converse/bot_configs/entity_extraction_config.yaml"
    )
    default_info_path = "./Converse/bot_configs/dial_info_config.yaml"
    default_entity_function_path = "./Converse/bot_configs/entity_function.py"

    def __init__(
        self,
        info_path: str = None,
        task_path: str = None,
        policy_path: str = None,
        entity_path: str = None,
        entity_extraction_path: str = None,
        response_path: str = None,
        entity_function_path: str = None,
    ):
        self.info_path = info_path or self.default_info_path
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
        self.task_config = TaskConfig(self.task_path)
        self.faq_config = FAQConfig(self.task_path)
        self.faq_exact_match_questions = []
        self.faq_exact_match_q2a_dict = {}
        for faq in self.faq_config:
            if "fuzzy_matching" in self.faq_config[faq].question_match_options:
                for question in self.faq_config[faq].samples:
                    self.faq_exact_match_questions.append(question.lower())
                    self.faq_exact_match_q2a_dict[question.lower()] = self.faq_config[
                        faq
                    ].answers
        self.policy = load_dial_logic(self.policy_path)
        self.info_layer: InfoManager = InfoManager(
            self.info_path, self.task_config, self.faq_config
        )
        self.entity_manager = EntityManager(
            self.entity_path, self.entity_extraction_path
        )
        self.policy_layer = DialoguePolicy(
            self.response_path,
            self.policy_path,
            self.task_path,
            self.entity_path,
            self.entity_extraction_path,
            self.entity_function_path,
        )

    def reset(self, initiate_user_input=True) -> str:
        """
        Forget all the history and let the bot start a new conversation.
        Reset orchestrator, dialog context and the policy layer.
        """
        self.task_config = TaskConfig(self.task_path)
        self.faq_config = FAQConfig(self.task_path)
        self.info_layer: InfoManager = InfoManager(
            self.info_path, self.task_config, self.faq_config
        )
        self.entity_manager = EntityManager(self.entity_path)
        self.policy_layer = DialoguePolicy(
            self.response_path,
            self.policy_path,
            self.task_path,
            self.entity_path,
            self.entity_extraction_path,
            self.entity_function_path,
        )
        response = self.policy_layer.response.greeting() if initiate_user_input else ""
        return response

    def store_agent_response(self, ctx: DialogContext):
        user_id = "spk2"
        message_time = "%Y-%m-%d %H:%M:%S"
        ctx.store_utt(user_id, message_time, ctx.last_response)

    def process(self, asr_origin: str, asr_norm: str, ctx: DialogContext) -> str:
        """
        aggregate the results from info layer and entity module,
        send current dialogue states to policy layer and get response
        """
        log.info("USER: %s", asr_norm)
        ctx.user_response = asr_norm
        # one turn represents of a pair of user response and agent response
        ctx.turn += 1
        faq_res = ""
        if asr_norm == "RESET":
            return self.reset()

        if ctx.finish_and_fail:
            ctx.last_response = self.policy_layer.response.forward_to_human()
            self.store_agent_response(ctx)
            return ctx.last_response

        cur_turn_states = StatesWithinCurrentTurn()
        if not asr_norm:
            return self.policy_layer.empty_response(ctx, cur_turn_states)
        cur_turn_states.asr_out = asr_norm

        pause_res = self.pause_detection(ctx, cur_turn_states)
        if pause_res:
            return pause_res

        self.policy_layer.state_manager.update_and_get_states(ctx)

        if ctx.cur_states.exceed_max_turn and not ctx.cur_states.cur_task:
            ctx.last_response = self.policy_layer.response.forward_to_human()
            self.store_agent_response(ctx)
            return ctx.last_response
        elif ctx.cur_states.exceed_max_turn and ctx.cur_states.prev_tasks:
            prev_res = self.policy_layer.response.task_finish_response(
                ctx.cur_states.prev_tasks,
                ctx.cur_states.prev_tasks_success,
                ctx.cur_states.prev_task_finish_func_response,
            )
            ctx.cur_states.prev_task_finish_func_response = ""
        else:
            prev_res = None

        self.extracted_info = self.info_layer.info_pipeline(asr_origin, asr_norm, ctx)
        cur_turn_states.extracted_info = self.extracted_info
        log.info(f"Extracted info: {self.extracted_info}")
        # somehow, email entity type is marked as 'DUCKLING/email'
        # while we expect 'EMAIL'
        # we manually change it here for now, but later we probably want to
        # change it in the NER server
        if self.extracted_info["ner"] and "probabilities" in self.extracted_info["ner"]:
            for ner_candidate in self.extracted_info["ner"]["probabilities"]:
                if ner_candidate["label"] == "DUCKLING/email":
                    ner_candidate["label"] = "EMAIL"

        # entity_candidates obtained from the user that are associated with the
        # current task
        entity_extraction_methods = self.entity_manager.get_extraction_methods(
            entity_name=ctx.cur_states.cur_entity_name,
        )
        expected_entity_classes = self.entity_manager.get_entity_classes(
            entity_name=ctx.cur_states.cur_entity_name,
        )

        self.entity_candidates = self.entity_manager.extract_entities(
            utterance=ctx.user_response,
            methods=entity_extraction_methods,
            ner_model_output=self.extracted_info["ner"],
            entity_types=expected_entity_classes,
        )
        cur_turn_states.entity_candidates = self.entity_candidates

        # add entities into the entity history manager
        for entity in self.entity_candidates:
            entity.turn = ctx.turn
            ctx.entity_history_manager.insert(entity, ctx.turn)

        cur_turn_states.got_info = cur_turn_states.got_entity_info = bool(
            self.entity_candidates
        )
        if not cur_turn_states.got_info:
            cur_turn_states.got_info = (
                cur_turn_states.got_entity_info
            ) = cur_turn_states.got_ner = (
                "probabilities" in self.extracted_info["ner"]
            )

        cur_turn_states.got_FAQ = (
            True
            if self.extracted_info["final_intent"]
            and self.extracted_info["final_intent"]["intent"]
            and self.extracted_info["final_intent"]["intent"] in self.faq_config
            else False
        )
        # exact match FAQ has higher priority than intent equivalent FAQ
        if self.faq_exact_match_questions:
            exact_match_question, exact_match_score = process.extract(
                asr_norm.lower(), self.faq_exact_match_questions, scorer=fuzz.ratio
            )[0]
            cur_turn_states.got_exact_FAQ = exact_match_score > 90
            if cur_turn_states.got_exact_FAQ:
                faq_res = choice(self.faq_exact_match_q2a_dict[exact_match_question])
                if not ctx.cur_states.cur_task:
                    ctx.tree_manager.finish = True
                # if current utterance is a exact match FAQ,
                # then the detected intent is probably wrong
                if self.extracted_info["final_intent"]:
                    self.extracted_info["final_intent"] = {
                        "intent": None,
                        "prob": 0.0,
                        "uncertain": False,
                    }
                cur_turn_states.got_entity_info = False
        if not cur_turn_states.got_exact_FAQ and cur_turn_states.got_FAQ:
            faq_res = choice(
                self.faq_config[self.extracted_info["final_intent"]["intent"]][
                    "answers"
                ]
            )
            cur_turn_states.got_entity_info = False
            if not ctx.cur_states.cur_task:
                ctx.tree_manager.finish = True

        if "USER_UTT" in ctx.cur_states.cur_entity_types:
            # we assume the whole user utterance is what we need for entity extraction
            cur_turn_states.got_intent = False
            if self.extracted_info["final_intent"]["intent"] == "positive":  # polarity
                ctx.cur_states.polarity = cur_turn_states.polarity = 1
            elif (
                self.extracted_info["final_intent"]["intent"] == "negative"
            ):  # polarity
                ctx.cur_states.polarity = cur_turn_states.polarity = -1
        else:
            cur_turn_states.got_intent = (
                True
                if self.extracted_info["final_intent"]
                and self.extracted_info["final_intent"]["intent"]
                and self.extracted_info["final_intent"]["intent"] in self.task_config
                else False
            )

            if cur_turn_states.got_intent:  # got new intent
                if self.extracted_info["final_intent"]["uncertain"]:
                    ctx.cur_states.confirm_intent = True
                    ctx.cur_states.unconfirmed_intent.append(
                        self.extracted_info["final_intent"]["intent"]
                    )
                    ctx.last_response = self.policy_layer.ask_confirm_task(
                        self.extracted_info["final_intent"]["intent"],
                        ctx,
                        cur_turn_states,
                    )
                    cur_turn_states.got_intent = True
                    self.store_agent_response(ctx)
                    ctx.cur_states.prev_turn_got_intent = cur_turn_states.got_intent
                    return ctx.last_response
                ctx.cur_states.new_task = self.extracted_info["final_intent"]["intent"]
                if ctx.cur_states.new_task == "positive":  # polarity
                    cur_turn_states.polarity = 1
                    cur_turn_states.got_intent = False
                    ctx.cur_states.new_task = None
                elif ctx.cur_states.new_task == "negative":  # polarity
                    cur_turn_states.polarity = -1
                    cur_turn_states.got_intent = False
                    ctx.cur_states.new_task = None
                else:
                    ctx.cur_states.confirm_continue = False
                    if ctx.cur_states.new_task not in ctx.cur_states.task_stack:
                        cur_turn_states.got_info = cur_turn_states.got_intent = True
                    else:
                        cur_turn_states.got_intent = False
                        ctx.cur_states.new_task = None
            else:
                cur_turn_states.polarity = 0
                ctx.cur_states.new_task = None

        if ctx.cur_states.multiple_entities:
            got_entity, entity = self.policy_layer.choose_entity(ctx, cur_turn_states)
            if got_entity:
                cur_turn_states.got_info = cur_turn_states.got_entity_info = True
            else:
                cur_turn_states.got_info = cur_turn_states.got_entity_info = False
        ctx.cur_states.polarity = cur_turn_states.polarity
        self._continuous_no_info_turn_handler(ctx, cur_turn_states)
        policy_res = self.policy_layer.policy_tree(self.policy, ctx, cur_turn_states)
        res = ""
        if prev_res:
            res += prev_res + " "
        if faq_res:
            res += faq_res + " "
        if policy_res:
            res += policy_res
            ctx.last_response = res
            self.store_agent_response(ctx)
        else:
            policy_res = self.policy_layer.empty_response(ctx, cur_turn_states)
            res += policy_res
        log.info("RES: %s", res)
        log.info(f"cur_states = {ctx.cur_states.to_dictionary()}")
        ctx.cur_states.prev_turn_got_intent = cur_turn_states.got_intent
        return res

    def _reset_continuous_no_info_turn_flag(self, ctx: DialogContext):
        """
        If got info in current turn, set continuous_no_info_turn and
        prev_turn_no_info to default value
        """
        ctx.cur_states.continuous_no_info_turn = 0
        ctx.cur_states.prev_turn_no_info = False
        return

    def _update_continuous_no_info_turn_flag(self, ctx: DialogContext):
        """
        If didn't get info in current turn, update continuous_no_info_turn and
        prev_turn_no_info flag
        """
        if ctx.cur_states.prev_turn_no_info:
            ctx.cur_states.continuous_no_info_turn += 1
        else:
            ctx.cur_states.continuous_no_info_turn = 1
            ctx.cur_states.prev_turn_no_info = True
        return

    def _continuous_no_info_turn_handler(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn
    ):
        """
        Update continuous_no_info_turn and prev_turn_no_info flag based on
        cur_turn_states.got_info. Check policy config file for more details,
        all the continuous no info turns are labeled there.
        """
        if cur_turn_states.got_info:
            self._reset_continuous_no_info_turn_flag(ctx)
        else:
            if not ctx.cur_states.cur_task and ctx.cur_states.confirm_continue:
                self._reset_continuous_no_info_turn_flag(ctx)
            else:
                self._update_continuous_no_info_turn_flag(ctx)
        return

    def pause_detection(
        self, ctx: DialogContext, cur_turn_states: StatesWithinCurrentTurn, model=False
    ) -> str:
        if not model:

            def fuzzy_check(keywords: list, threshold=3):
                utter = cur_turn_states.asr_out.lower()
                for k in keywords:
                    res = find_near_matches(k, utter, max_l_dist=threshold)
                    if len(res) > 0:
                        return True
                return False

            hold_keywords = [
                "hold a second",
                "hold a sec",
                "hold a 2nd",
                "hold a moment",
                "wait a second",
                "wait a sec",
                "wait a 2nd",
                "wait a moment",
            ]

            resume_keywords = [
                "okay I'm back",
                "ok i'm back",
                "i'm back ok" "i'm back",
                "i am back",
            ]
            if not ctx.do_pause:
                if fuzzy_check(hold_keywords):
                    ctx.do_pause = True
                    return "sure"
            if ctx.do_pause:
                if fuzzy_check(resume_keywords):
                    ctx.do_pause = False
                    return self.policy_layer.welcome_back(ctx)
                else:
                    return self.policy_layer.empty_response(ctx, cur_turn_states)


if __name__ == "__main__":
    import sys
    import uuid
    from Converse.dialog_context.dialog_context_manager import DialogContextManager

    dmgr = DialogContextManager.new_instance("memory")
    orc = Orchestrator(
        info_path="Converse/bot_configs/dial_info_config.yaml",
        task_path="Converse/bot_configs/health_appointment/tasks.yaml",
        policy_path="Converse/bot_configs/policy_config.yaml",
        entity_path="Converse/bot_configs/health_appointment/entity_config.yaml",
        entity_extraction_path="Converse/bot_configs/entity_extraction_config.yaml",
        response_path="Converse/bot_configs/response_template.yaml",
    )
    cid = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
    print(f"you conversation id is {cid}")
    ctx = dmgr.reset_ctx(
        cid,
        orc.policy_layer.state_manager.entity_manager.entity_config,
        orc.policy_layer.state_manager.task_config,
        orc.policy_layer.bot_config,
    )
    res = orc.reset()
    dmgr.save(cid, ctx)
    print("Agent:", res)
    while True:
        sent = input("User: ")
        ctx = dmgr.get_or_create_ctx(
            cid,
            orc.policy_layer.state_manager.entity_manager.entity_config,
            orc.policy_layer.state_manager.task_config,
            orc.policy_layer.bot_config,
        )
        res = orc.process(sent, sent, ctx)
        dmgr.save(cid, ctx)
        print("Agent:", res)
