# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

try:  # Try to use LibYAML, a fast open-sourced YAML parser and emitter written in C
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:  # Default PyYAML parser
    from yaml import Loader, Dumper

import Converse.entity_backend.entity_functions as ef
from Converse.utils.yaml_parser import load_yaml, save_yaml

import traceback
import json
import logging
from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
import os
import argparse
import uuid
from datetime import datetime
import glob
from werkzeug.utils import secure_filename

from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.dialog_context.dialog_context_manager import DialogContextManager

app = Flask(__name__, template_folder="./templates")
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ["tmpl"]


@app.route("/")
def builder():
    ts = datetime.now().timestamp()
    return render_template("builder.html", ts=ts)


def function_names():
    function_names = []
    skip = {"requests", "TimeSeries", "timeout", "resp", "process", "fuzz"}
    for func in dir(ef):
        if func not in skip and not func.startswith("__"):
            function_names.append(func)

    return function_names


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return {"status": "error", "msg": "file not found"}

    file = request.files["file"]
    if file.filename == "":
        return {"status": "error", "msg": "empty file name"}

    filetype = request.form["type"]
    filename = secure_filename(file.filename)
    upload_folder = args.config_dir
    filepath = os.path.join(upload_folder, filename)

    path = args.task_path
    if filetype == "entity":
        path = args.entity_path
    elif filetype == "policy":
        path = args.policy_path
    elif filetype == "response":
        path = args.response_path

    if file and filepath == path + ".tmpl":
        file.save(filepath)
        return {
            "status": "ok",
            "msg": "uploaded " + filetype + " template file:" + filename,
        }
    else:
        return {
            "status": "error",
            "msg": "Wrong file format, expect " + os.path.basename(path + ".tmpl"),
        }


@app.route("/saveTree", methods=["POST"])
@cross_origin()
def save_tree():
    user_input = request.json
    file = request.args.get("file")
    if not user_input or not file:
        return {"status": "error", "msg": "Missing parameters"}

    if not file:
        file = "task"

    path = args.task_path
    if file == "entity":
        path = args.entity_path
    elif file == "policy":
        path = args.policy_path
    elif file == "response":
        path = args.response_path
    timestamp = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
    os.rename(path, path + "." + timestamp)
    return {"status": "ok", "msg": "Saved", "response": save_yaml(user_input, path)}


@app.route("/tree", methods=["GET"])
def load_tree():
    file = request.args.get("file")
    timestamp = request.args.get("ts")

    path = args.task_path

    if not file:
        file = "task"

    if file == "entity":
        path = args.entity_path
    elif file == "policy":
        path = args.policy_path
    elif file == "response":
        path = args.response_path

    tmpl = path + ".tmpl"

    history = glob.glob(path + ".2*")

    if timestamp:
        path = path + "." + timestamp

    try:
        data = load_yaml(path)
    except Exception as e:
        data = {}

    try:
        tmpl = load_yaml(tmpl)
    except Exception as e:
        tmpl = []

    return {
        "status": "ok",
        "data": data,
        "tmpl": tmpl,
        "file": path,
        "functions": function_names(),
        "history": history,
    }


# dial_backend


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


def printException():
    msg = traceback.format_exc()
    app.logger.info(msg)
    print(msg)
    return traceback.format_exc(limit=1)


@app.route("/process", methods=["POST"])
def predict():
    user_input = request.json
    if "text" not in user_input or "cid" not in user_input:
        return json.dumps({"action": "ERROR"})

    cid = user_input["cid"]

    try:
        ctx = dmgr.get_or_create_ctx(
            cid,
            orchestrator.policy_layer.state_manager.entity_manager.entity_config,
            orchestrator.policy_layer.state_manager.task_config,
            orchestrator.policy_layer.bot_config,
        )
        res = orchestrator.process(user_input["text"], user_input["text"], ctx)
        dmgr.save(cid, ctx)
    except Exception as e:
        msg = printException()
        return {"status": "error", "msg": msg}

    return json.dumps({"response": res})


@app.route("/dialog_status/<cid>", methods=["GET"])
def showtree(cid):
    try:
        ctx = dmgr.get_ctx(cid)
        if not ctx:
            return json.dumps({"Info": "session not initialized."})
        tree_data = ctx.tree_manager.task_tree.tree_show()
    except Exception as e:
        msg = printException()
        return {"status": "error", "msg": msg}

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


print("Initializing Smart Builder ...")
app.logger.info("Initializing Smart Builder ...")
# LOGLEVEL=[debug|info|warning|error|critical] \
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(filename="./converse.log", level=LOGLEVEL, format=FORMAT)
CORS(app)

app.logger.info("done!")

parser = argparse.ArgumentParser("Converse config UI")
parser.add_argument(
    "--config_dir",
    type=str,
    default="./Converse/bot_configs/ui_yamls/",
)
parser.add_argument(
    "--response_path",
    type=str,
    default="./Converse/bot_configs/ui_yamls/response_template.yaml",
)
parser.add_argument(
    "--policy_path",
    type=str,
    default="./Converse/bot_configs/ui_yamls/policy_config.yaml",
)
parser.add_argument(
    "--task_path",
    type=str,
    default="./Converse/bot_configs/ui_yamls/merged_task_entity.yaml",
)
parser.add_argument(
    "--entity_path",
    type=str,
    default="./Converse/bot_configs/ui_yamls/merged_task_entity.yaml",
)
parser.add_argument("--entity_extraction_path", type=str, default=None)
parser.add_argument("--info_path", type=str, default=None)
parser.add_argument("--entity_function_path", type=str, default=None)

args, unknown = parser.parse_known_args()

try:
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
except Exception as e:
    printException()

if __name__ == "__main__":
    app.run("0.0.0.0", port=8088)
