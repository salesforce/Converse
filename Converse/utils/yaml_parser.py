# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

# Description: parsing tasks yaml file.
from copy import deepcopy
from yaml import load, dump

try:  # Try to use LibYAML, a fast open-sourced YAML parser and emitter written in C
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:  # Default PyYAML parser
    from yaml import Loader, Dumper


def load_yaml(filename: str):
    """
    Load contents of a yaml file in a dictionary
    :param filename: path to the yaml file
    :return: a data object contains contents of the yaml file
    """
    with open(filename, "r") as f:
        data_stream = f.read()
    return load(data_stream, Loader=Loader)


def save_yaml(data, filename):
    """
    Save a data object into a yaml file
    :param data: a data object
    :param filename: the path to the yaml file
    :return: None, the yaml file will be saved
    """
    with open(filename, "w") as f:
        dump(data, f, default_flow_style=False, sort_keys=False, Dumper=Dumper)


def load_data(filename: str, data_type):
    """
    Load data from yaml file according to a specific data type
    :param filename: the path to the yaml file
    :param data_type: the data type
    :return: a data object
    """
    data = load_yaml(filename)
    return data[data_type] if data_type in data else None


def load_dial_logic(filename: str):
    return load_data(filename, "Logic")


def load_entity(filename):
    return load_data(filename, "Entity")


def load_entity_extraction(filename):
    return load_data(filename, "Entity Extraction")


def load_info_logic(filename: str):
    return load_data(filename, "Models")


def load_response(filename):
    return load_data(filename, "Response")


def load_tasks(filename):
    return load_data(filename, "Task")


def load_bot_config(filename):
    return load_data(filename, "Bot")


def load_FAQ_config(filename):
    return load_data(filename, "FAQ")


def merge_task_entity_yamls(
    task_config_path: str, entity_config_path: str, merged_path: str
):
    """
    Merge task yaml file and entity yaml file into a task-entity yaml
    file.
    :param task_config_path: the path to the task yaml file
    :param entity_config_path: the path to the entity yaml file
    :param merged_path: the output path of the merged yaml file
    :return: None, the merged yaml file will be saved
    """
    task_dict = load_yaml(task_config_path)
    entity_dict = load_yaml(entity_config_path)

    for task in task_dict["Task"]:
        if "entities" in task_dict["Task"][task]:
            for entity in task_dict["Task"][task]["entities"]:
                if "type" in entity_dict["Entity"][entity]:
                    task_dict["Task"][task]["entities"][entity]["type"] = entity_dict[
                        "Entity"
                    ][entity]["type"]
                if "methods" in entity_dict["Entity"][entity]:
                    task_dict["Task"][task]["entities"][entity]["methods"] = deepcopy(
                        entity_dict["Entity"][entity]["methods"]
                    )
                if "suggest_value" in entity_dict["Entity"][entity]:
                    task_dict["Task"][task]["entities"][entity][
                        "suggest_value"
                    ] = entity_dict["Entity"][entity]["suggest_value"]

    save_yaml(task_dict, merged_path)


def get_entity_from_task_config(task_dict: dict):
    """
    Extract task-specific entity config from task config dict
    :param task_dict: a dictionary contains task config
    :return: a dictionary contains entity config
    """
    entity_dict = dict()
    entity_dict["Entity"] = dict()

    for task in list(task_dict.keys()):
        if "entities" in task_dict[task]:
            for entity in task_dict[task]["entities"]:
                if entity not in entity_dict["Entity"]:
                    entity_dict["Entity"][entity] = dict()
                    if "type" in task_dict[task]["entities"][entity]:
                        entity_dict["Entity"][entity]["type"] = task_dict[task][
                            "entities"
                        ][entity]["type"]
                    if "methods" in task_dict[task]["entities"][entity]:
                        entity_dict["Entity"][entity]["methods"] = deepcopy(
                            task_dict[task]["entities"][entity]["methods"]
                        )
                    if "suggest_value" in task_dict[task]["entities"][entity]:
                        entity_dict["Entity"][entity]["suggest_value"] = task_dict[
                            task
                        ]["entities"][entity]["suggest_value"]
    return entity_dict


def split_task_entity_yamls(
    task_entity_config_path, task_config_path, entity_config_path
):
    """
    Split a merged task-entity yaml file into seperated task yaml
    file and entity yaml file
    :param task_entity_config_path: the path to the merged yaml file
    :param task_config_path: the path to the task yaml file
    :param entity_config_path: the path to the entity yaml file
    :return: None, task yaml file and entity yaml file will be saved
    """
    task_entity_dict = load_tasks(task_entity_config_path)
    task_dict = deepcopy(task_entity_dict)

    for task in list(task_dict.keys()):
        if "entities" in task_dict[task]:
            for entity in task_dict[task]["entities"]:
                if "type" in task_dict[task]["entities"][entity]:
                    del task_dict[task]["entities"][entity]["type"]
                if "methods" in task_dict[task]["entities"][entity]:
                    del task_dict[task]["entities"][entity]["methods"]
                if "suggest_value" in task_dict[task]["entities"][entity]:
                    del task_dict[task]["entities"][entity]["suggest_value"]

    entity_dict = get_entity_from_task_config(task_entity_dict)

    save_yaml(task_dict, task_config_path)
    save_yaml(entity_dict, entity_config_path)
