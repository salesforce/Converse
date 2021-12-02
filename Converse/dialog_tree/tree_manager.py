# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging
from collections import deque

from Converse.dialog_tree.dial_tree import TaskTree
from Converse.config.task_config import TaskConfig


log = logging.getLogger(__name__)


class TreeManager:
    """Handles all tree related operations including tree building and traversal.

    For dial_state_manager.StateManager to take tree related operations.

    After updating entity info on the tree, StateManager should call
    TreeManager.traverse() to get the updated cur_node and cur_entity.

    If there's new task, StateManager should call TreeManager.set_task(task_name) to
    set the task and call TreeManager.traverse() to initialize the cur_node
    and cur_entity.

    If cur_task exceeds max turn, StateManager can force it to finish by calling
    TreeManager.force_finish_task(). No need to call traverse() again after
    calling force_finish_task().

    StateManager should call reset_prev_task() each time after receiving information
    from dial_policy.DialPolicy.


    Attributes:
        task_config (str): File path to task configuration yaml file.
        task_tree (dial_tree.TaskTree): Task Tree built by the task file.
        task_stack (:obj:'list' of :obj: 'str'): List of tasks in the order that
            they are created.
        cur_task (str): Current task name.
            Can be modified by functions set_task, _switch_task, _check_task
        cur_node (dial_tree.Leaf): Current node under the current task.
        cur_entity (str): Current entity name under the current node.
        finish (bool): True if current task tree is finished, false otherwise.
            Can be modified by by functions _check_task, set_task
        finished_node (:obj:'set' of :obj: 'dial_tree.AndNode'
            /'dial_tree.OrNode'/'dial_tree.Leaf'): List of finished tree node.
            Can be modified by by functions _unfinished_node, _switch_node, _set_entity
        parent_dicts (:obj:'dict' of :obj: 'dial_tree.AndNode'
            /'dial_tree.OrNode'/'dial_tree.Leaf'): Key is child node,
            value is parrent node.
        prev_tasks (list): Previously finished tasks in the order that they finished in.
        prev_tasks_success (list): A list that is the same length as self.prev_tasks
            where an entry is True when the task at the same index in self.prev_tasks
            finished successfully and False otherwise.

    """

    def __init__(self, task_config: TaskConfig):
        self.task_path = task_config
        self.task_tree = TaskTree(task_config)
        self.task_stack = []
        self.cur_task = None
        self.cur_node = None
        self.cur_entity = None
        self.finish = False
        self.finished_node = set()
        self.parent_dicts = {}
        self.prev_node = None
        self.prev_tasks = []
        self.prev_tasks_success = []

    def update_entity(self, entity_value, status=True):
        """
        Update entity value for the current entity.
        """
        if not self.cur_node:
            return
        self.cur_node.info[self.cur_entity] = entity_value
        if self.cur_node.cnt:
            for en in self.cur_node.info:
                self.cur_node.expand.add(en)
        else:
            self.cur_node.expand.add(self.cur_entity)
        if status:
            self.cur_node.verified.add(self.cur_entity)
            if self.cur_entity in self.cur_node.wrong:
                self.cur_node.wrong.remove(self.cur_entity)
        elif entity_value is not None:
            self.cur_node.wrong.add(self.cur_entity)

    def set_current_entity(self):
        """For visualization"""
        if not self.cur_node:
            return
        self.update_entity(None, False)
        if self.prev_node:
            self.prev_node.current = None
            self.cur_node.current = self.cur_entity
            self.prev_node = self.cur_node
        else:
            self.cur_node.current = self.cur_entity
            self.prev_node = self.cur_node

    @property
    def prev_task_finished(self):
        """bool: True if the zeroth element in prev_tasks is in self.finished_node
        and False otherwise.
        """
        if not self.prev_tasks:
            return False
        prev_task = self.prev_tasks[0]
        return (
            prev_task in self.task_tree.root.child
            and self.task_tree.root.child[prev_task] in self.finished_node
        )

    def reset_states(self):
        """
        Reset all of the states in the tree manager.
        """
        self.task_tree = TaskTree(self.task_path)
        self.task_stack = []
        self.cur_task = None
        self.cur_node = None
        self.cur_entity = None
        self.finish = False
        self.finished_node = set()
        self.parent_dicts = {}
        self.reset_prev_task()

    def reset_prev_task(self):
        """
        Resets the instance variables associated with the previous task.
        """
        self.prev_tasks = []
        self.prev_tasks_success = []

    def next(self, asr_out):
        """
        only for unit test
        """
        self.unit_test_leaf_handler(asr_out)
        res = self.traverse()
        if res:
            log.info(
                "cur_task: %s,cur_node: %s, cur_entity: %s",
                self.cur_task,
                self.cur_node,
                self.cur_entity,
            )
            log.info("task_stack %s", self.task_stack)
            # print(self.parent_dicts)

    def unit_test_leaf_handler(self, asr_out):
        """
        only for unit test
        """
        assert self.cur_task
        assert self.cur_node
        assert self.cur_entity
        if asr_out == "yes":
            self.update_entity("True")
        if asr_out == "no":
            self.update_entity("False", False)
        if asr_out == "new task":
            pass

    def traverse(self):
        """The traversal function for dialogue manager.

        Must use after setting cur_task.
        You can use self.set_task to initialize cur_task.

        Returns:
            (
                dial_tree.Leaf: cur_node,
                str: cur_entity
            )

        """
        assert not self.finish, "current task is finished!"
        assert self.cur_task, "no current task!"
        if not self.cur_node:
            self.cur_node = self.task_tree.root.child[self.cur_task]
            self._set_entity()
            self.set_current_entity()
            return (self.cur_node, self.cur_entity)
        else:
            if self._unfinished_node(self.cur_node):
                self._next_entity()
                self.set_current_entity()
                return (self.cur_node, self.cur_entity)
            else:
                self._check_task()
                if self.finish:
                    self._empty_task_handler()
                    return None
                else:
                    if self.cur_node:
                        self._switch_node()
                    else:
                        self.cur_node = self.task_tree.root.child[self.cur_task]
                    self._set_entity()
                    self.set_current_entity()
                    return (self.cur_node, self.cur_entity)

    def _switch_node(self):
        """Switch self.cur_node from a leaf node to another leaf node.

        In each call, either set self.cur_node to another node under
        the same parent node, or set self.cur_node to current parent
        node if there's no avaliable leaf node under the current parent node.
        After using this function, should use _set_entity to set the first
        entity under this node.

        """
        self._check_task()
        assert self.cur_task
        assert self.cur_node
        if self.cur_task not in self.parent_dicts:
            self._parent_helper(self.cur_task)
        p = self.parent_dicts[self.cur_task][self.cur_node]
        p_type = p.__class__.__name__
        if p_type == self.task_tree.and_node:
            for c in p.child:
                c_node = p.child[c]
                if c_node():  # c_node is successed
                    continue
                else:  # c_node is failed
                    if c_node in self.finished_node:  # c_node is seen
                        self.finished_node.add(p)
                        p.success = False
                        self.cur_node = p
                        self._switch_node()
                        return
                    else:  # c_node is unseen
                        self.cur_node = c_node
                        return
            # no avaliable node under current parent node
            self.finished_node.add(p)
            p.success = True
            self.cur_node = p
            if p.name == self.cur_task:
                self.task_stack.pop()
            self._switch_node()
        if p_type == self.task_tree.or_node:
            for c in p.child:
                c_node = p.child[c]
                if c_node():
                    self.finished_node.add(p)
                    p.success = True
                    self.cur_node = p
                    self._switch_node()
                    return
                else:
                    if c_node in self.finished_node:
                        continue
                    else:
                        self.cur_node = c_node
                        return
            self.finished_node.add(p)
            p.success = False
            self.cur_node = p
            if p.name == self.cur_task:
                self.task_stack.pop()
            self._switch_node()

    def _set_entity(self):
        """A recursive function to find next leaf node, set the next entity under current node.

        Use after _switch_node unless initialize cur_entity.
        If no available node/entity,
        will return False and add related nodes to self.finished_node.

        Return:
            True if set cur_entity successfully;
            False if there's no available node or entity.

        """
        assert self.cur_node
        node_type = self.cur_node.__class__.__name__
        if (
            (self.cur_node.name in self.task_tree.tasks)
            and (self.task_stack[-1] != self.cur_node.name)
            and (not self.cur_node())
            and self.cur_node not in self.finished_node
        ):
            self.task_stack.append(self.cur_node.name)
        self.cur_task = self.task_stack[-1]
        # and node
        if node_type == self.task_tree.and_node:
            rec_flag = False
            for c in self.cur_node.child:
                c_node = self.cur_node.child[c]
                c_type = self.cur_node.child[c].__class__.__name__
                if not c_node():
                    if c_node not in self.finished_node:  # unseen and false
                        if c_type == self.task_tree.leaf_node:
                            self.cur_node = c_node
                            self._next_entity()
                            return True
                        else:  # complex structure
                            rec_flag = True
                            self.cur_node = c_node
                            self._set_entity()
                            break
                    else:  # seen and false
                        self.cur_node.success = False
                        self.finished_node.add(self.cur_node)
                        return False
                else:
                    continue
            if not rec_flag:
                self.finished_node.add(self.cur_node)
            return False
        # or node
        elif node_type == self.task_tree.or_node:
            rec_flag = False
            for c in self.cur_node.child:
                c_node = self.cur_node.child[c]
                c_type = self.cur_node.child[c].__class__.__name__
                if not c_node():
                    if c_node not in self.finished_node:  # unseen and false
                        if c_type == self.task_tree.leaf_node:
                            self.cur_node = c_node
                            self._next_entity()
                            return True
                        else:  # complex structure
                            rec_flag = True
                            self.cur_node = c_node
                            self._set_entity()
                            break
                    else:  # seen and false
                        continue
                else:
                    self.cur_node.success = True
                    self.finished_node.add(self.cur_node)
                    return False
            if not rec_flag:
                self.finished_node.add(self.cur_node)
            return False
        # leaf node
        elif node_type == self.task_tree.leaf_node:
            self._next_entity()
            return True

    def _unfinished_node(self, node):
        """Check whether a leaf node is finished.

        Used on leaf node.
        If all the entities are seen:
            the node is finished, return False
        if some entities are seen,
            some entities are wrong, and we need to verify all the entities:
                the node is finished, return False
            some entities are wrong, and the wrong count is greater than allowed:
                the node is finished, return False
            some entities are wrong, and the wrong count is smaller than allowed:
                the node is unfinished, stay in the same node and go to next entity,
                return True
        if no entity is seen:
            the node is unfinished,
            stay in the same node and go to next entity,
            return True

        Return:
            True if should stay in current node;
            False if should go to next node.

        """
        assert node.__class__.__name__ == self.task_tree.leaf_node
        # when we have to verify all the entities in the group
        if node.cnt == 0:
            for en in node.info:
                if en in node.wrong:
                    self.finished_node.add(node)
                    return False
                else:
                    if not self.cur_node.info[en]:
                        return True
            self.finished_node.add(node)
            return False
        # when we don't have to verify all the entities,
        # we may stay at the current node and go to next entity
        else:
            allow_cant_verify = len(self.cur_node.info) - self.cur_node.cnt
            unseen_entity_flag = False
            verified_entity = 0
            for en in node.info:
                if not node.info[en]:
                    if en in node.wrong:
                        allow_cant_verify -= 1
                        if allow_cant_verify < 0:
                            self.finished_node.add(node)
                            return False
                    else:
                        unseen_entity_flag = True
                else:
                    if en in node.wrong:
                        allow_cant_verify -= 1
                        if allow_cant_verify < 0:
                            self.finished_node.add(node)
                            return False
                    else:
                        verified_entity += 1
            if verified_entity >= self.cur_node.cnt:
                self.finished_node.add(node)
                return False
            else:
                if unseen_entity_flag:
                    return True
            self.finished_node.add(node)
            return False

    def _next_entity(self):
        """Get next entity in current node.

        Must be used on unfinished node.

        """
        assert self.cur_node
        for en in self.cur_node.info:
            if not self.cur_node.info[en] and (en not in self.cur_node.wrong):
                self.cur_entity = en
                break

    def _traverse_vis_helper(self):
        self.set_current_entity()

    def _parent_helper(self, task):
        parent_dict = {}
        queue = deque([self.task_tree.root.child[task]])
        nextqueue = deque([])
        # bfs
        if task not in self.parent_dicts:
            while queue:
                node = queue.popleft()
                node_type = node.__class__.__name__
                if node_type != self.task_tree.leaf_node:
                    for c in node.child:
                        parent_dict[node.child[c]] = node
                        nextqueue.append(node.child[c])
                if not queue:
                    queue = nextqueue
                    nextqueue = deque([])
            self.parent_dicts[task] = parent_dict

    def _check_task(self):
        """A function to update current task status.

        Check whether cur_task node should be add to self.finished_node,
        if yes, either set self.finish to True or switch to the next available task.
        Used before _switch_node and after _switch_task.
        (Only these 2 operations can lead to finishing a task)

        if current task is succeeded (prev_task_success) \
            or the current task failed but is finished using _finished_task():

            add current task node to self.finished_node, remove it from the task_stack,
            and set the current node and current entity to None.
            update prev_tasks and prev_tasks_success for the current task

            if there's no task in task stack:
                set self.finish to True
            else:
                call _switch_task
                new self.cur_task will be set,
                self.cur_node and self.cur_entity will be reset to None
        """
        prev_task_success = self.task_tree.root.child[self.cur_task]()
        if prev_task_success or self._finished_task(
            self.task_tree.root.child[self.cur_task]
        ):
            self.finished_node.add(self.task_tree.root.child[self.cur_task])
            self.task_stack.pop()
            self.cur_node = None
            self.cur_entity = None
            # We want to save the previous task before the next if statement block
            # because the code inside the if statement block might change self.cur_task.
            self.prev_tasks.append(self.cur_task)
            self.prev_tasks_success.append(prev_task_success)
            if not self.task_stack:
                self.finish = True
                self.cur_task = None
                self._empty_task_handler()
            else:
                self._switch_task()

    def _finished_task(self, node):
        """A function for _check_task() to check whether current task is finished.

        Used after calling the cur_task node,
        so the success flag for each node is already up to date,
        and the leaf nodes are already added to
        self.finished_node in self._unfinished_node,
        so here we only update the and/or nodes to self.finished_node.
        If current task is finished,
        add current task node to self.finished_node.

        Return:
            True if current task is finished, False otherwise.

        """
        if node in self.finished_node:
            return True
        level_dict = self._level_helper(node)
        depth = len(level_dict)
        for level in range(depth - 1, -1, -1):
            level_nodes = level_dict[level]
            for node in level_nodes:
                if node.success:
                    self.finished_node.add(node)
                    continue
                node_type = node.__class__.__name__
                if node_type == self.task_tree.leaf_node:
                    continue
                if node_type == self.task_tree.and_node:
                    for c in node.child:
                        c_node = node.child[c]
                        if (
                            not c_node() and c_node in self.finished_node
                        ):  # seen and false
                            self.finished_node.add(node)
                            break
                if node_type == self.task_tree.or_node:
                    unseen_flag = False
                    for c in node.child:
                        c_node = node.child[c]
                        if (
                            not c_node() and c_node not in self.finished_node
                        ):  # unseen and false
                            unseen_flag = True
                    if not unseen_flag:
                        self.finished_node.add(node)
        return True if node in self.finished_node else False

    def _level_helper(self, node):
        """A helper function for _finished_task()

        Return a dict of failed nodes on different level.
        (not including nodes under a finished node)
        Or let's say, return a dict of nodes
        that possibly will be affected by the nodes under it.

        """
        level_dict = {}
        queue = deque([node])
        next_queue = deque([])
        level = 0
        # bfs
        while queue:
            node = queue.popleft()
            if node():
                self.finished_node.add(node)
            else:
                if node not in self.finished_node:
                    if level not in level_dict:
                        level_dict[level] = []
                    level_dict[level].append(node)
                    if node.__class__.__name__ != self.task_tree.leaf_node:
                        for c in node.child:
                            next_queue.append(node.child[c])
            if not queue:
                queue = next_queue
                next_queue = deque([])
                level += 1
        return level_dict

    def _switch_task(self):
        """Set new self.cur_task, self.cur_node and self.cur_entity.

        Use after _check_task()

        """
        assert self.task_stack
        self.cur_task = self.task_stack[-1]
        self.cur_node = None
        self.cur_entity = None
        if self.cur_task not in self.parent_dicts:
            self._parent_helper(self.cur_task)
        self._check_task()

    def set_task(self, task_name):
        self.cur_node = None
        self.cur_entity = None
        self.cur_task = task_name
        if self.cur_task in self.parent_dicts:
            del self.parent_dicts[self.cur_task]
        self.task_stack.append(self.cur_task)
        self.task_tree.build_subtree(self.cur_task)
        self.finish = False

    def _empty_task_handler(self):
        """
        only for unit test
        should be some action in dialogue manager
        """
        # print("Current task is finished!")

    def force_finish_task(self):
        """If the num of turns excess the max_turn, force current task to be finished.

        if all the task are finished:
            will set self.finish to True,
            reset self.cur_task, self.cur_entity and self.entity to None
        else:
            find the next task, node, entity
            and set self.cur_task, self.cur_entity and self.entity accordingly
        """
        self.finished_node.add(self.task_tree.root.child[self.cur_task])
        self._check_task()
        if self.finish:
            self._empty_task_handler()
        else:
            self.cur_node = self.task_tree.root.child[self.cur_task]
            self._set_entity()
            self.set_current_entity()


if __name__ == "__main__":
    dm = TreeManager()
    dm.set_task("check_order")
    cur_node, cur_entity = dm.traverse()
    while True:
        sent = input("User:")
        if sent == "RESET":
            dm.reset_states()
            dm.set_task("check_order")
            dm.traverse()
            print(
                "cur_task:" + str(dm.cur_task),
                "cur_node:" + str(dm.cur_node),
                "cur_entity:" + str(dm.cur_entity),
            )
        else:
            dm.next(sent)
