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
import uuid
from datetime import datetime
import glob
from werkzeug.utils import secure_filename

from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.dialog_context.dialog_context_manager import DialogContextManager


def create_config_ui_app(
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
    log_path="./converse.log",
):
    """
    Set up the config ui flask service.
    The function is almost the same with config_ui_backend.py.

    Attributes:
        template_folder: the path for template folder
        static_folder: the path for static folder
    """
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

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
        upload_folder = config_dir
        filepath = os.path.join(upload_folder, filename)

        path = task_path
        if filetype == "entity":
            path = entity_path
        elif filetype == "policy":
            path = policy_path
        elif filetype == "response":
            path = response_path

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

        path = task_path
        if file == "entity":
            path = entity_path
        elif file == "policy":
            path = policy_path
        elif file == "response":
            path = response_path
        timestamp = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
        os.rename(path, path + "." + timestamp)
        return {"status": "ok", "msg": "Saved", "response": save_yaml(user_input, path)}

    @app.route("/tree", methods=["GET"])
    def load_tree():
        file = request.args.get("file")
        timestamp = request.args.get("ts")

        path = task_path

        if not file:
            file = "task"

        if file == "entity":
            path = entity_path
        elif file == "policy":
            path = policy_path
        elif file == "response":
            path = response_path

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
    LOGLEVEL = os.environ.get("LOGLEVEL", "info").upper()
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    logging.basicConfig(filename=log_path, level=LOGLEVEL, format=FORMAT)
    CORS(app)

    app.logger.info("done!")

    try:
        dmgr = DialogContextManager.new_instance("memory")
        orchestrator = Orchestrator(
            response_path=response_path,
            policy_path=policy_path,
            task_path=task_path,
            entity_path=entity_path,
            entity_extraction_path=entity_extraction_path,
            info_path=info_path,
            entity_function_path=entity_function_path,
        )
    except Exception as e:
        printException()
    app.run("0.0.0.0", port=8088)
