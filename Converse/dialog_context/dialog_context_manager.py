# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging
import redis

from Converse.dialog_context.dialog_context import DialogContext
from Converse.config.task_config import TaskConfig, BotConfig

log = logging.getLogger(__name__)


class DialogContextManager:
    @staticmethod
    def new_instance(ctx_mgr_name: str, **kwargs) -> "DialogContextManager":
        """Factory method to instantiate dialog context manager."""
        if ctx_mgr_name == "memory":
            return MemoryDialogContextManager()
        elif ctx_mgr_name == "redis":
            return RedisDialogContextManager(**kwargs)
        raise ValueError("context manager should be [memory|redis]")

    def get_ctx(self, ctx_key: str) -> DialogContext:
        raise NotImplementedError

    def get_or_create_ctx(
        self,
        ctx_key: str,
        entity_config: dict,
        task_config: TaskConfig,
        bot_config: BotConfig,
    ) -> DialogContext:
        raise NotImplementedError

    def delete_ctx(self, ctx_key: str) -> DialogContext:
        raise NotImplementedError

    def _set_ctx(self, ctx_key: str, ctx_value: DialogContext):
        raise NotImplementedError

    def reset_ctx(
        self,
        ctx_key: str,
        entity_config: dict,
        task_config: TaskConfig,
        bot_config: BotConfig,
    ) -> DialogContext:
        raise NotImplementedError

    def save(self, ctx_key: str, ctx_value: DialogContext):
        pass


class MemoryDialogContextManager(DialogContextManager):
    def __init__(self):
        """
        MemoryDialogContextManager keeps dialogue contexts in memory.
        so it is requried that requests from a client are served by the
        same server node.
        """
        self.context_store = {}
        super().__init__()

    def get_ctx(self, ctx_key: str) -> DialogContext:
        return self.context_store.get(ctx_key)

    def get_or_create_ctx(
        self,
        ctx_key: str,
        entity_config: dict = None,
        task_config: TaskConfig = None,
        bot_config: BotConfig = None,
    ) -> DialogContext:
        if ctx_key in self.context_store:
            return self.context_store.get(ctx_key)
        else:
            ctx_value = DialogContext(
                entity_config=entity_config,
                task_config=task_config,
                bot_config=bot_config,
            )
            self._set_ctx(ctx_key, ctx_value)
            return ctx_value

    def reset_ctx(
        self,
        ctx_key: str,
        entity_config: dict = None,
        task_config: TaskConfig = None,
        bot_config: BotConfig = None,
    ) -> DialogContext:
        ctx_value = DialogContext(
            entity_config=entity_config, task_config=task_config, bot_config=bot_config
        )
        self._set_ctx(ctx_key, ctx_value)
        return ctx_value

    def delete_ctx(self, ctx_key: str):
        return self.context_store.pop(ctx_key, None)

    def _set_ctx(self, ctx_key: str, ctx_value: DialogContext):
        self.context_store[ctx_key] = ctx_value


class RedisDialogContextManager(DialogContextManager):
    def __init__(self, **kwargs):
        """
        RedisDialogContextManager keeps dialogue contexts in Redis.
        """
        host = kwargs.get("host", "127.0.0.1")
        port = kwargs.get("port", 6379)
        self.context_store = redis.Redis(host=host, port=port)
        super().__init__()

    def get_ctx(self, ctx_key: str) -> DialogContext:
        if self.context_store.exists(ctx_key):
            serialized_ctx_value = self.context_store.get(ctx_key)
            return DialogContext.deserialize(serialized_ctx_value)
        else:
            return None

    def get_or_create_ctx(
        self,
        ctx_key: str,
        entity_config: dict = None,
        task_config: TaskConfig = None,
        bot_config: BotConfig = None,
    ) -> DialogContext:
        if self.context_store.exists(ctx_key):
            serialized_ctx_value = self.context_store.get(ctx_key)
            return DialogContext.deserialize(serialized_ctx_value)
        else:
            ctx_value = DialogContext(
                entity_config=entity_config,
                task_config=task_config,
                bot_config=bot_config,
            )
            self._set_ctx(ctx_key, ctx_value)
            return ctx_value

    def reset_ctx(
        self,
        ctx_key: str,
        entity_config: dict = None,
        task_config: TaskConfig = None,
        bot_config: BotConfig = None,
    ) -> DialogContext:
        ctx_value = DialogContext(
            entity_config=entity_config, task_config=task_config, bot_config=bot_config
        )
        self._set_ctx(ctx_key, ctx_value)
        return ctx_value

    def _set_ctx(self, ctx_key: str, ctx_value: DialogContext):
        serialized_ctx_value = ctx_value.serialize()
        self.context_store.set(ctx_key, serialized_ctx_value)

    def delete_ctx(self, ctx_key: str):
        return self.context_store.delete(ctx_key)

    def save(self, ctx_key: str, ctx_value: DialogContext):
        self._set_ctx(ctx_key, ctx_value)
