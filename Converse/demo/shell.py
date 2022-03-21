# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import os
import subprocess
import time

from Converse.demo.setup_config_ui import create_config_ui_app
from Converse.utils.config_yaml_generator import YamlGenerator, receive_user_input
from Converse.utils.utils import resp


UI_FOLDER = os.path.join(os.getcwd(), "Converse/demo")


def main():
    print("Hello, Converse!")
    print(resp(True, "This is a test"))


def download_files(yaml_dir="./Converse/bot_configs"):
    """
    The function copies the Converse/bot_configs folder from Converse Github repo to
    a user-specified dir,
    and copies Converse/demo/templates, Converse/demo/static folder from Github to
    local Converse/demo/templates, Converse/demo/static
    """
    subprocess.run(
        [
            "svn",
            "checkout",
            "https://github.com/salesforce/Converse/trunk/Converse/bot_configs",
            yaml_dir,
        ]
    )
    subprocess.run(
        [
            "svn",
            "checkout",
            "https://github.com/salesforce/Converse/trunk/Converse/demo/templates",
            os.path.join(UI_FOLDER, "templates"),
        ]
    )
    subprocess.run(
        [
            "svn",
            "checkout",
            "https://github.com/salesforce/Converse/trunk/Converse/demo/static",
            os.path.join(UI_FOLDER, "static"),
        ]
    )
    subprocess.run(
        [
            "wget",
            "https://raw.githubusercontent.com/salesforce/Converse/main/Converse/demo/chat_window_app.py"
        ]
    )


def get_models_status():
    ner_status = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "myner"],
        capture_output=True,
        text=True,
    ).stdout.strip("\n")
    intent_status = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "myintent"],
        capture_output=True,
        text=True,
    ).stdout.strip("\n")
    return ner_status == "true" and intent_status == "true"


def set_up_ner_and_intent_model():
    """
    To set up the NLU services via docker images.
    Requires installing and opening docker.
    """
    # set up ner service
    ner_process = subprocess.Popen(
        [
            "docker",
            "run",
            "--name",
            "myner",
            "-p",
            "50051:50051",
            "converseallresearch/ner:0.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    # set up intent service
    intent_process = subprocess.Popen(
        [
            "docker",
            "run",
            "--name",
            "myintent",
            "-p",
            "9001:9001",
            "converseallresearch/intent:0.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )


def ask_for_yaml_dir(first_time=True):
    """
    To get a user specified path to save all the configuration files.
    """
    if first_time:
        yaml_dir = input(
            "- Input the path that you would like to use "
            "to save all the configuration files, "
            "\ndefault is a new folder named "
            "Converse/bot_configs under the current dir"
            "\n: "
        )
    else:
        yaml_dir = input(
            "- Input the path you saved all the configuration files, "
            "\ndefault is a folder named Converse/bot_configs under the current dir"
            "\n: "
        )
    if not yaml_dir:
        yaml_dir = "./Converse/bot_configs"
    return yaml_dir


def build():
    """
    For the first time user to build a bot from scratch.
    """
    first_time = input(
        "- Is this the first time you use this project? "
        "\nIf yes, I would be happy to help you download all the configuration files "
        "you need and set up the NLU model services."
        "\nOtherwise you can skip the above steps and directly build the bot!"
        "\n(input y/n, default is y):"
    )
    first_time = convert_boolean_value(var=first_time, default_value=True)

    # step 1: specify the yaml dir
    yaml_dir = ask_for_yaml_dir(first_time)

    # step 2: download all the configuration files
    if first_time:
        download_files(yaml_dir)

    # step 3: set up NLU service
    if not first_time:
        have_nlu_models = input(
            "- Have you set up the NLU models? "
            "\nIf you haven't, please make sure you've installed and opened Docker."
            "\nSee https://docs.docker.com/get-docker/ for reference."
            "\n(input y/n, default is n):"
        )
        have_nlu_models = convert_boolean_value(
            var=have_nlu_models, default_value=False
        )
    if first_time or not have_nlu_models:
        set_up_ner_and_intent_model()
        while not get_models_status():
            time.sleep(1.0)

    # step 4: choose between the 2 different ways to build the first bot
    building_method = input(
        "- Input 1 if you would like to use the UI "
        "to build the first bot(recommended), "
        "\ninput 2 if you would like to directly modify the yaml files, "
        "\n(default is 1):"
    )
    if building_method == "2":
        # step 5-2: generate template configuration files
        config_generator = YamlGenerator(yaml_dir)
        receive_user_input(config_generator)
        ready = input(
            "- Input anything when you finish modifying the configuration files, "
            "\na chat window will be set up for you to test your new bot!"
            "\n:"
        )
        subprocess.run(
            [
                "python",
                os.path.join(os.getcwd(), "chat_window_app.py"),
                "--response_path=" + os.path.join(yaml_dir, "response_template.yaml"),
                "--policy_path=" + os.path.join(yaml_dir, "policy_config.yaml"),
                "--task_path=" + os.path.join(yaml_dir, "tasks.yaml"),
                "--entity_path=" + os.path.join(yaml_dir, "entity_config.yaml"),
                "--entity_extraction_path="
                + os.path.join(yaml_dir, "entity_extraction_config.yaml"),
                "--info_path=" + os.path.join(yaml_dir, "dial_info_config.yaml"),
                "--entity_function_path="
                + os.path.join(yaml_dir, "entity_function.py"),
            ]
        )
    else:
        building_method = "1"
        # step 5-1: set up config UI
        print("- Please open your browser and go to http://localhost:8088")
        set_up_config_ui(
            config_dir=yaml_dir,
            response_path=os.path.join(yaml_dir, "ui_yamls/response_template.yaml"),
            policy_path=os.path.join(yaml_dir, "ui_yamls/policy_config.yaml"),
            task_path=os.path.join(yaml_dir, "ui_yamls/merged_task_entity.yaml"),
            entity_path=os.path.join(yaml_dir, "ui_yamls/merged_task_entity.yaml"),
            entity_extraction_path=os.path.join(
                yaml_dir, "entity_extraction_config.yaml"
            ),
            info_path=os.path.join(yaml_dir, "dial_info_config.yaml"),
            entity_function_path=os.path.join(yaml_dir, "entity_function.py"),
            template_folder=os.path.join(UI_FOLDER, "templates"),
            static_folder=os.path.join(UI_FOLDER, "static"),
        )


def convert_boolean_value(var, default_value):
    if var.strip().lower() == "y":
        converted_var = True
    elif var.strip().lower() == "n":
        converted_var = False
    else:
        converted_var = default_value
    return converted_var


def demo():
    """
    For the first time user to chat with the template bots.
    """
    first_time = input(
        "- Is this the first time you use this project?"
        "\nIf yes, I would be happy to help you download all the configuration files "
        "you need and set up the NLU model services. "
        "\nOtherwise you can skip the above steps and directly try the bot!"
        "\n(input y/n, default is y):"
    )
    first_time = convert_boolean_value(var=first_time, default_value=True)
    # step 1: specify the yaml dir
    yaml_dir = ask_for_yaml_dir(first_time)

    # step 2: download all the configuration files
    if first_time:
        download_files(yaml_dir)

    # step 3: set up NLU service
    if not first_time:
        have_nlu_models = input(
            "- Have you set up the NLU models? "
            "\nIf you haven't, please make sure you've installed and opened Docker."
            "\nSee https://docs.docker.com/get-docker/ for reference."
            "\n(input y/n, default is n):"
        )
        have_nlu_models = convert_boolean_value(
            var=have_nlu_models, default_value=False
        )
    if first_time or not have_nlu_models:
        set_up_ner_and_intent_model()
        while not get_models_status():
            time.sleep(1.0)

    # step 4: set up the chat window
    template_bot_name = input(
        "- We have several template bots for you to try, "
        "\n1. online shopping"
        "\n2. health appointment"
        "\n3. book movie ticket"
        "\n4. online banking"
        "\n5. customize a t-shirt"
        "\n6. book a flight"
        "\nplease input the number of the bot you're interested in:"
        "\n(default is 1):"
    )
    print("- Please open your browser and go to http://localhost:9002/client")
    set_up_demo_bots(yaml_dir, template_bot_name)


def set_up_demo_bots(yaml_dir, template_bot_name):
    """
    A wrapper function to excute chat_window_app.py so we can set up template bots by name.
    """

    response_path = os.path.join(yaml_dir, "response_template.yaml")
    policy_path = os.path.join(yaml_dir, "policy_config.yaml")
    task_path = os.path.join(yaml_dir, "health_appointment/tasks.yaml")
    entity_path = os.path.join(yaml_dir, "health_appointment/entity_config.yaml")
    entity_extraction_path = os.path.join(yaml_dir, "entity_extraction_config.yaml")
    info_path = os.path.join(yaml_dir, "dial_info_config.yaml")
    entity_function_path = os.path.join(yaml_dir, "entity_function.py")
    template_folder = os.path.join(UI_FOLDER, "templates")
    static_folder = os.path.join(UI_FOLDER, "static")

    # change the necessary variables
    if template_bot_name == "2":
        task_path = os.path.join(yaml_dir, "health_appointment/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "health_appointment/entity_config.yaml")
    elif template_bot_name == "3":
        task_path = os.path.join(yaml_dir, "book_movie_tickets/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "book_movie_tickets/entity_config.yaml")
    elif template_bot_name == "4":
        task_path = os.path.join(yaml_dir, "banking/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "banking/entity_config.yaml")
    elif template_bot_name == "5":
        task_path = os.path.join(yaml_dir, "manufacturing/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "manufacturing/entity_config.yaml")
    elif template_bot_name == "6":
        response_path = os.path.join(yaml_dir, "book_flights/response_template.yaml")
        task_path = os.path.join(yaml_dir, "book_flights/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "book_flights/entity_config.yaml")
    else:
        template_bot_name = "1"
        task_path = os.path.join(yaml_dir, "online_shopping/tasks.yaml")
        entity_path = os.path.join(yaml_dir, "online_shopping/entity_config.yaml")
    subprocess.run(
        [
            "python",
            os.path.join(os.getcwd(), "chat_window_app.py"),
            "--response_path=" + response_path,
            "--policy_path=" + policy_path,
            "--task_path=" + task_path,
            "--entity_path=" + entity_path,
            "--entity_extraction_path=" + entity_extraction_path,
            "--info_path=" + info_path,
            "--entity_function_path=" + entity_function_path,
        ]
    )


def set_up_config_ui(
    config_dir,
    response_path,
    policy_path,
    task_path,
    entity_path,
    entity_extraction_path,
    info_path,
    entity_function_path,
    template_folder,
    static_folder,
):
    print("setting up config UI...")
    create_config_ui_app(
        config_dir=config_dir,
        response_path=response_path,
        policy_path=policy_path,
        task_path=task_path,
        entity_path=entity_path,
        entity_extraction_path=entity_extraction_path,
        info_path=info_path,
        entity_function_path=entity_function_path,
        template_folder=template_folder,
        static_folder=static_folder,
    )
