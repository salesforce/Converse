# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from Converse.entity.entity import extract_display_value_from_entity
from Converse.config.task_config import TaskConfig
from collections import defaultdict


class Leaf:
    def __init__(self, name="E", tag="INFORM", cnt=0):
        """A group of entities"""
        self.name = name
        self.info = {}
        self.tag = tag
        self.cnt = cnt  # 0 means all

        # For visualization
        self.verified = set()
        self.wrong = set()
        self.expand = set()
        self.success = False
        self.current = None

    def __call__(
        self, *args, **kwargs
    ):  # Here we only use Tree Structure to store information
        if self.success:
            return True
        if self.cnt == 0:
            for k in self.info:
                if not self.info[k] or k in self.wrong:
                    return False
            self.success = True
            return True
        else:
            cnt_true = 0
            for k in self.info:
                if self.info[k] and k in self.verified:
                    cnt_true += 1
                    if cnt_true >= self.cnt:
                        self.success = True
                        return True
            return False

    def update(self, key, value):
        self.info[key] = value


class OrNode:
    def __init__(self, name=""):
        self.name = name
        self.child = {}
        self.success = False

    def __call__(self, *args, **kwargs):
        if self.success:
            return True
        for node in self.child:
            if self.child[node]():
                self.success = True
                return True
        return False


class AndNode:
    def __init__(self, name=""):
        self.name = name
        self.child = {}
        self.success = False

    def __call__(self, *args, **kwargs):
        if self.success:
            return True
        for node in self.child:
            if not self.child[node]():
                return False
        self.success = True
        return True


class TaskTree:
    def __init__(self, task_config: TaskConfig):
        """
        This class defines the data structure for task tree.
        Attributes:
            self._task_config: task configuration info loaded from task yaml files
            self.root: the root node of the task tree
            self.tree_paths: root node to leaf nodes paths represented in a dictionary
            self.entity_paths: built from self.tree_paths, for each entity, we store
                the path from root to itself so that we can update it in constant time
            self.tasks: task config for each task we built in the task tree
            self.tree_json: json data represents the tree structure for visualization
            self.task_set: task names in the task tree
            self.visualization_paths: we use this to generate tree_json
            self.task_order: the order of all tasks we tried to built
            self.prev_entity: store the previous entity to undo enlargement
                 of the circle representing the entity in visualization when switch
                 to a new entity.
            self.parent_to_children_paths: we store each task's sub-task for each
                building sub-task action, no task's sub-task should be built more
                than once in a single build_subtask call.
        """
        self._tasks_config = task_config
        self.root = OrNode("root")
        self.tree_paths = {}
        self.entity_paths = {}
        self.tasks = {}
        self.tree_json = None
        self.task_set = set()
        self.visualization_paths = {}
        self.task_order = []
        self.prev_entity = None
        self.parent_to_children_paths = defaultdict(list)

        self.entity_types = {
            "INFORM",
            "VERIFY",
            "UPDATE",
            "DELETE",
            "INSERT",
            "QUERY",
            "API",
            "SIMPLE",
        }
        # Agent action types
        self.__inform = "INFORM"
        self.__verify = "VERIFY"
        self.__update = "UPDATE"
        self.__delete = "DELETE"
        self.__insert = "INSERT"
        self.__query = "QUERY"
        self.__api = "API"
        self.__simple = "SIMPLE"

        # Node types
        self.__leaf_node = Leaf.__name__
        self.__and_node = AndNode.__name__
        self.__or_node = OrNode.__name__

    @property
    def simple(self):
        return self.__simple

    @property
    def inform(self):
        return self.__inform

    @property
    def api(self):
        return self.__api

    @property
    def verify(self):
        return self.__verify

    @property
    def update(self):
        return self.__update

    @property
    def delete(self):
        return self.__delete

    @property
    def insert(self):
        return self.__insert

    @property
    def query(self):
        return self.__query

    @property
    def leaf_node(self):
        return self.__leaf_node

    @property
    def and_node(self):
        return self.__and_node

    @property
    def or_node(self):
        return self.__or_node

    def _tree_reset(self):
        self.root = OrNode("root")
        self.tree_paths = {}
        self.tasks = {}
        self.tree_json = None
        self.task_set = set()

        self.visualization_paths = {}
        self.task_order = []
        self.prev_entity = None

        self.parent_to_children_paths = defaultdict(list)
        self.tree_show()

    def _cycle_detection(self, task, sub_task):
        if sub_task in self.parent_to_children_paths[task]:  # cycle detected
            self._tree_reset()
            raise RecursionError(
                "Task dependency cycle detected. "
                "Please check your task configuration file!"
            )
        self.parent_to_children_paths[task].append(sub_task)

    def build_subtree(self, task, start=True):
        """Given task name, build corresponding subtree"""
        condi = self._tasks_config[task].success
        if len(condi) != 1:
            raise ValueError("The success tree must have only one child")
        if start:
            if task in self.task_set:
                self.task_set.remove(task)
            self.parent_to_children_paths = defaultdict(list)

        self.tree_paths[task] = {}
        self.task_order.append(task)

        def build(data, ntype, paths):  # helper function
            if ntype == "TASK":
                info = data[ntype][0]  # task name
                paths[info] = "task"
                self._cycle_detection(task, info)
                if info not in self.root.child:
                    self.build_subtree(info, start=False)  # build subtree dependency
                node = self.root.child[info]

            elif ntype in self.entity_types:
                info = data[ntype][0].split("#")  # entity name, cnt
                if len(info) > 1 and info[1].isdigit():
                    num = int(info[1])
                else:
                    num = 0
                node = Leaf(info[0], ntype, num)
                value = self._tasks_config[task].entity_groups[info[0]]
                paths[info[0]] = {}
                for key in value:
                    paths[info[0]][key] = "entity"
                    node.update(key, None)

            elif ntype == "OR":
                if task not in self.task_set:
                    node = OrNode(task)
                    self.task_set.add(task)
                else:
                    node = OrNode()
                for i in range(len(data[ntype])):
                    new_data = data[ntype][i]
                    new_type = list(new_data.keys())[0]
                    paths[str(i)] = {}
                    node.child[str(i)] = build(
                        new_data, new_type, paths[str(i)]
                    )  # add child node

            elif ntype == "AND":
                if task not in self.task_set:
                    node = AndNode(task)
                    self.task_set.add(task)
                else:
                    node = AndNode()
                for i in range(len(data[ntype])):
                    new_data = data[ntype][i]
                    new_type = list(new_data.keys())[0]
                    paths[str(i)] = {}
                    node.child[str(i)] = build(
                        new_data, new_type, paths[str(i)]
                    )  # add child node
            else:
                raise ValueError("Not a valid ntype: %s" % ntype)
            return node

        self.root.child[task] = build(
            condi, list(condi.keys())[0], self.tree_paths[task]
        )  # dfs

        for task in self.tree_paths:  # add entity paths, initialize tasks

            # we do not want to modify the original task config, so we use copies
            self.tasks[task] = self._tasks_config[task].copy()

    def get_samples(self):
        samples = {}
        for task in self._tasks_config:
            samples[task] = (
                self._tasks_config[task].samples
                if "samples" in self._tasks_config[task]
                else []
            )
        return samples

    def get_description(self, task: str):
        return self._tasks_config[task].description

    def build_paths(self):
        """Tree Visualization"""

        def build_task_paths(node, paths, depth):
            ntype = node.__class__.__name__
            if ntype == "OrNode" or ntype == "AndNode":
                for c in node.child:
                    cnode = node.child[c]
                    ctype = cnode.__class__.__name__
                    if (
                        cnode.name in self.task_set and depth >= 1
                    ):  # depend on another task
                        new_type = "success" if cnode.success else ctype
                        paths.append(
                            {
                                "name": "(Task) " + cnode.name,
                                "parent": node.name,
                                "type": new_type,
                            }
                        )
                    else:
                        if ctype == "Leaf":
                            if cnode.cnt > 0:
                                new_name = (
                                    "(OR "
                                    + str(cnode.cnt)
                                    + ") "
                                    + cnode.tag
                                    + " "
                                    + cnode.name
                                )
                            else:
                                new_name = cnode.tag + " " + cnode.name
                            new_children = []
                            for en in cnode.expand:
                                if en in cnode.verified:
                                    new_child_info = {
                                        "name": en
                                        + ": "
                                        + extract_display_value_from_entity(
                                            cnode.info[en]
                                        ),
                                        "parent": cnode.name,
                                        "type": "success",
                                    }
                                elif en in cnode.wrong:
                                    if not cnode.info[en]:
                                        new_child_info = {
                                            "name": en,
                                            "parent": cnode.name,
                                        }
                                    else:
                                        new_child_info = {
                                            "name": en
                                            + ": "
                                            + extract_display_value_from_entity(
                                                cnode.info[en]
                                            ),
                                            "parent": cnode.name,
                                            "type": "failed",
                                        }
                                else:
                                    new_child_info = {"name": en, "parent": cnode.name}
                                if en == cnode.current:
                                    new_child_info["current"] = True
                                new_children.append(new_child_info)
                            if cnode.success:
                                paths.append(
                                    {
                                        "name": new_name,
                                        "parent": node.name,
                                        "type": "success",
                                        "children": new_children,
                                    }
                                )
                            elif cnode.cnt > 0:
                                paths.append(
                                    {
                                        "name": new_name,
                                        "parent": node.name,
                                        "type": "OrNode",
                                        "children": new_children,
                                    }
                                )
                            else:
                                paths.append(
                                    {
                                        "name": new_name,
                                        "parent": node.name,
                                        "type": "failed",
                                        "children": new_children,
                                    }
                                )
                        elif ctype == "OrNode" or ctype == "AndNode":
                            new_type = "success" if cnode.success else ctype
                            if ctype == "OrNode":
                                new_node_name = "(OR) " + cnode.name
                            else:
                                new_node_name = "(AND) " + cnode.name
                            paths.append(
                                {
                                    "name": new_node_name,
                                    "parent": node.name,
                                    "type": new_type,
                                    "children": [],
                                }
                            )
                            new_path = paths[-1]["children"]
                            build_task_paths(cnode, new_path, depth + 1)

        for task in self.task_order[::-1]:
            task_type = (
                "success"
                if self.root.child[task].success
                else self.root.child[task].__class__.__name__
            )
            node_name = task
            if self.root.child[task].__class__.__name__ == "OrNode":
                node_name = "(OR) " + task
            elif self.root.child[task].__class__.__name__ == "AndNode":
                node_name = "(AND) " + task
            self.visualization_paths[task] = {
                "name": node_name,
                "parent": "root",
                "type": task_type,
                "children": [],
            }
            build_task_paths(
                self.root.child[task], self.visualization_paths[task]["children"], 1
            )

    def tree_show(self):
        self.build_paths()
        self.tree_json = {
            "name": "root",
            "parent": "null",
            "children": [],
            "type": "OrNode",
        }
        for task in self.visualization_paths:
            self.tree_json["children"].append(self.visualization_paths[task])
        return self.tree_json
