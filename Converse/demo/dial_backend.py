# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import argparse
import json
import logging
import os
import traceback
import uuid

from flask import Flask, request, render_template
from flask_cors import CORS

from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.dialog_context.dialog_context_manager import DialogContextManager


app = Flask(__name__, template_folder="./templates/")


def printException():
    msg = traceback.format_exc()
    app.logger.info(msg)
    print(msg)
    return traceback.format_exc(limit=1)


@app.route("/reset", methods=["POST"])
def reset():
    """
    start a new conversation.
    """
    try:
        user_input = request.json
        if "cid" not in user_input:
            return json.dumps({"status": "ERROR"})

        res = orchestrator.reset()
        cid = user_input["cid"]
        ctx = dmgr.reset_ctx(
            cid,
            orchestrator.policy_layer.state_manager.entity_manager.entity_config,
            orchestrator.policy_layer.state_manager.task_config,
            orchestrator.policy_layer.bot_config,
        )
        dmgr.save(cid, ctx)
    except Exception as e:
        msg = printException()
        return json.dumps({"status": "ERROR", "msg": msg})

    return json.dumps({"status": "ok", "response": res})


@app.route("/process", methods=["POST"])
def predict():
    user_input = request.json
    if "text" not in user_input or "cid" not in user_input:
        return json.dumps({"action": "ERROR"})

    cid = user_input["cid"]
    ctx = dmgr.get_or_create_ctx(
        cid,
        orchestrator.policy_layer.state_manager.entity_manager.entity_config,
        orchestrator.policy_layer.state_manager.task_config,
        orchestrator.policy_layer.bot_config,
    )
    res = orchestrator.process(user_input["text"], user_input["text"], ctx)
    dmgr.save(cid, ctx)
    return json.dumps({"response": res})


@app.route("/dialog_status/<cid>", methods=["GET"])
def showtree(cid):
    ctx = dmgr.get_ctx(cid)
    if not ctx:
        return json.dumps({"Info": "session not initialized."})
    tree_data = ctx.tree_manager.task_tree.tree_show()
    return render_template("tree.html", tree=tree_data)


@app.route("/chat", methods=["GET"])
def run_client():
    say_hi = orchestrator.policy_layer.response.greeting()
    cid = str(uuid.uuid4())
    dmgr.get_or_create_ctx(
        cid,
        orchestrator.policy_layer.state_manager.entity_manager.entity_config,
        orchestrator.policy_layer.state_manager.task_config,
        orchestrator.policy_layer.bot_config,
    )
    return render_template("chat.html", greetings=say_hi, cid=cid)


@app.route("/client", methods=["GET"])
def index():
    bot_name = orchestrator.policy_layer.bot_config.bot_name
    return render_template("client.html", bot_name=bot_name)


def run():
    # LOGLEVEL=[debug|info|warning|error|critical] \
    # python ./dial_backend.py
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    logging.basicConfig(filename="./converse.log", level=LOGLEVEL, format=FORMAT)
    CORS(app)
    app.logger.info("Initializing Dial ...")
    app.logger.info("done!")
    app.run("0.0.0.0", port=9002)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Converse backend script")
    parser.add_argument("--response_path", type=str, default=None)
    parser.add_argument("--policy_path", type=str, default=None)
    parser.add_argument("--task_path", type=str, default=None)
    parser.add_argument("--entity_path", type=str, default=None)
    parser.add_argument("--entity_extraction_path", type=str, default=None)
    parser.add_argument("--info_path", type=str, default=None)
    parser.add_argument("--entity_function_path", type=str, default=None)
    args = parser.parse_args()

    dmgr = DialogContextManager.new_instance("memory")
    orchestrator = Orchestrator(
        response_path=args.response_path,
        policy_path=args.policy_path,
        task_path=args.task_path,
        entity_path=args.entity_path,
        entity_extraction_path=args.entity_extraction_path,
        info_path=args.info_path,
        entity_function_path=args.entity_function_path,
    )
    run()
