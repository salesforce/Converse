# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging
import jsonpickle
from collections import deque

from Converse.dialog_state_manager.dial_state_manager import DialogState
from Converse.dialog_tree.tree_manager import TreeManager
from Converse.entity.entity_history import EntityHistoryManager
from Converse.config.task_config import TaskConfig, BotConfig


log = logging.getLogger(__name__)


class UserHistory:
    def __init__(self):
        self.messages_buffer = deque()
        self.user_utt_norm = []
        self.sys_response = []
        self.model_res = {}

    def store_message(
        self, user_id, message_time, utt, tokenized_text="", pos_tags=[], model_res={}
    ):
        mes = Message(user_id, message_time, utt, model_res)
        if user_id == "spk1":
            self.user_utt_norm.append(utt)
        elif user_id == "spk2":
            self.sys_response.append(utt)
        self.messages_buffer.append(mes)

    def store_result(self, model_res, message_ind=-1):
        mes = self.messages_buffer[message_ind]
        mes.model_results = model_res

    def extract_utt(self, win_size=4):
        """
        extract the context to resolve coreference, return list of Message
        """
        res = []
        win_size = min(win_size, len(self.messages_buffer))
        for i in range(len(self.messages_buffer) - 1, -1, -1):
            msg = self.messages_buffer[i]
            res.append(msg)
            win_size -= 1
            if win_size == 0:
                break
        res = res[::-1]
        return res


class Message:
    def __init__(
        self,
        user_id,
        message_time,
        raw_text,
        tokenized_text="",
        pos_tags=None,
        model_results=None,
    ):
        self.user_id = user_id  # type: str
        self.message_time = message_time  # type: str
        self.raw_text = raw_text  # type: str
        self.tokenized_text = tokenized_text
        self.text_with_negation_words_removed = raw_text
        self.utt_replaced_coref = raw_text
        self.pos_tags = pos_tags
        self.model_results = model_results

    def __repr__(self):
        return (
            "user_id: "
            + self.user_id
            + " raw_text: "
            + self.raw_text
            + " message_time: "
            + self.message_time
        )


class DialogContext:
    def __init__(
        self, entity_config: dict, task_config: TaskConfig, bot_config: BotConfig
    ):
        """
        DialogContext records the meta data for a dialog session.
        """
        self.user_response = ""  # saves the latest user response
        self.turn = 0
        self.last_response = None
        self.do_pause = False
        self.finish_and_fail = False
        self.repeat = False
        self.update_entity = dict()
        self.policy_map = dict()
        self.bot_config = bot_config
        # policy map stores string mapping from strings in config yaml
        # file to strings represent the actual variables and functions,
        # like “confirm_entity” -> “ctx.cur_states.confirm_entity”
        self.cur_states: DialogState = None
        if bool(entity_config):
            self.cur_states = DialogState()
        self.tree_manager = TreeManager(task_config)
        self.tree_manager.reset_states()
        self.entity_history_manager = EntityHistoryManager()
        self.entity_history_manager.reset()
        self.user_history = UserHistory()
        self.collected_entities = dict()
        self.reset_update()

    def serialize(self) -> str:
        return jsonpickle.encode(self)

    @staticmethod
    def deserialize(serialized_dialog_context: str) -> "DialogContext":
        """
        Construct DialogContext object from serialized text. This applies
        to RedisContextManager whose DialogueContext object must be serialized
        before calling set_ctx and deserialized after calling get_ctx.

        Args:
            serialized_text (str): the serialized DialogContext object.

        Returns:
            An DialogContext instance.
        """
        dialog_context = jsonpickle.decode(serialized_dialog_context)
        assert isinstance(dialog_context, DialogContext)
        return dialog_context

    def store_utt(self, user_id, message_time, utt, **kwags):
        self.user_history.store_message(user_id, message_time, utt, **kwags)

    def store_res(self, model_res):
        self.user_history.store_result(model_res)

    def reset_update(self):
        """
        self.update_entity keeps track of the entity extracted from the entity
        history or user utterance.
        - self.update_entity["entity"] is the name of the entity, e.g. zip_code
        - self.update_entity["value"] is the value of the entity, e.g. 94301
        - self.update_entity["task"] is the name of the current task when the
          entity was extracted, e.g. verify_user
        """
        self.update_entity["entity"] = None
        self.update_entity["value"] = None
        self.update_entity["task"] = None


if __name__ == "__main__":
    dialog_context = DialogContext(
        {},
        TaskConfig("./Converse/bot_configs/tasks.yaml"),
        BotConfig("./Converse/bot_configs/tasks.yaml"),
    )
    dialog_context.turn += 1
    encoded_string = dialog_context.serialize()
    origin = DialogContext.deserialize(encoded_string)
    assert origin.turn == 1
