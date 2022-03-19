import argparse
import json
import os
import logging
import traceback
import uuid
import requests
from flask import Flask, request, render_template, Blueprint
from flask_cors import CORS
from wrapt_timeout_decorator import timeout

from Converse.utils.utils import json_resp
from Converse.simple_db.simple_db import SimpleDB
from Converse.dialog_orchestrator.orchestrator import Orchestrator
from Converse.dialog_context.dialog_context_manager import DialogContextManager

chat_window = Blueprint(
    "chat_window",
    __name__,
    static_folder=os.path.join(os.getcwd(), "Converse/demo/static"),
    template_folder=os.path.join(os.getcwd(), "Converse/demo/templates"),
)


def printException():
    msg = traceback.format_exc()
    app.logger.info(msg)
    print(
        "Unfortunately, an error has occurred during the process. "
        "Please refer to the log."
    )
    return traceback.format_exc(limit=1)


@chat_window.route("/reset", methods=["POST"])
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


@chat_window.route("/process", methods=["POST"])
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


@chat_window.route("/dialog_status/<cid>", methods=["GET"])
def showtree(cid):
    ctx = dmgr.get_ctx(cid)
    if not ctx:
        return json.dumps({"Info": "session not initialized."})
    tree_data = ctx.tree_manager.task_tree.tree_show()
    return render_template("tree.html", tree=tree_data)


@chat_window.route("/chat", methods=["GET"])
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


@chat_window.route("/client", methods=["GET"])
def index():
    bot_name = orchestrator.policy_layer.bot_config.bot_name
    return render_template("client.html", bot_name=bot_name)


entity_service = Blueprint(
    "entity_service",
    __name__,
    static_folder=os.path.join(os.getcwd(), "Converse/demo/static"),
    template_folder=os.path.join(os.getcwd(), "Converse/demo/templates"),
)

# There are several APIs modified from the functions in entity_functions.py .
# These APIs are examples for the entity services.


@timeout(0.1)
@entity_service.route("/inch_2_cm", methods=["POST"])
def funcInch2Cm():
    dm_msg = request.json["entities"]
    entity_name = "inch"
    inch = float(dm_msg[entity_name])
    cm = 2.54 * inch
    return json_resp(True, "{} inch equals to {} centimeter".format(inch, cm))


@timeout(1.0)
@entity_service.route("/get_weather", methods=["POST"])
def funcGetWeather():
    def getWeather(zipcode):
        apiKey = "69b8a3eca4a62e882f77a03275ce31a7"
        url = (
            "http://api.openweathermap.org/data/2.5/weather?zip={},us&appid={}".format(
                zipcode, apiKey
            )
        )
        r = requests.get(url).json()
        loc = r["name"]
        weather = r["weather"][0]["description"]
        return weather, loc

    dm_msg = request.json["entities"]
    entity_name = "zip_code"
    zipcode = dm_msg[entity_name]
    if isinstance(zipcode, tuple):
        address = dict(zipcode)
        zipcode = " ".join(address.values())

    try:
        res = getWeather(zipcode)
        return json_resp(
            True,
            "Weather condition is {} at {}, {}".format(res[0], res[1], zipcode),
        )
    except Exception:
        return json_resp(
            False, msg="Weather condition not availiable at {}".format(zipcode)
        )


@timeout(0.1)
@entity_service.route("/get_tv_plan", methods=["POST"])
def funcGetTVPlanPrice():
    dm_msg = request.json["entities"]
    entity_name = "new_tv_plan"
    tvplan = dm_msg[entity_name]
    price = {"hulu live": 200, "hulu tv": 200, "fubo tv": 300, "pluto tv": 500}
    try:
        return json_resp(
            True,
            "the price of {} is {} dollar per year".format(tvplan, price[tvplan]),
        )
    except Exception:
        return json_resp(False, msg="the price of {} is not avaiable".format(tvplan))


@timeout(0.5)
@entity_service.route("/single_step_verify", methods=["POST"])
def single_step_verify():
    entities = request.json["entities"]
    cur_entity = request.json["cur_entity"]
    try:
        verify_res = simple_db.single_step_verify(entities, cur_entity)
        if verify_res:
            return json_resp(verify_res, msg="Verified")
        else:
            return json_resp(verify_res, msg="Verify failed")
    except Exception as e:
        print(e)
        return json_resp(False, msg="Verify failed")


@timeout(0.5)
@entity_service.route("/get_order_status", methods=["POST"])
def get_order_status():
    try:
        entities = request.json["entities"]
        oid = entities["oid"]
        order_res = simple_db.get_order_status(oid)
        if order_res != "ERROR":
            return json_resp(True, msg=order_res)
        else:
            return json_resp(False, msg=order_res)
    except Exception as e:
        print(e)
        return json_resp(False, msg="Error")


@timeout(0.5)
@entity_service.route("/query_order", methods=["POST"])
def query_order():
    try:
        entities = request.json["entities"]
        oid = int(entities["oid"])
        query_res = simple_db.query_order(oid)
        if query_res != "None":
            return json_resp(True, msg=query_res)
        else:
            return json_resp(False, msg=query_res)
    except Exception:
        return json_resp(False, msg="None")


@timeout(0.5)
@entity_service.route("/add_more_to_order", methods=["POST"])
def add_more_to_order():
    try:
        entities = request.json["entities"]
        oid = int(entities["oid"])
        value = int(entities["quantity"])
        add_more_res = simple_db.add_more_to_order(oid, value)
        if add_more_res != "ERROR":
            return json_resp(True, msg=add_more_res)
        else:
            return json_resp(False, msg=add_more_res)
    except Exception:
        return json_resp(False, msg="ERROR")


@entity_service.route("/testdb", methods=["GET"])
def test_db():
    res = simple_db.test_db()
    # entities = {'email_address': 'peter0@hotmail.com'}
    # res = simple_db._verify_user(entities)
    return json_resp(False, msg=f"{res}")


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument(
        "--task_path", default="./Converse/bot_configs/online_shopping/tasks.yaml"
    )
    my_parser.add_argument(
        "--entity_path",
        default="./Converse/bot_configs/online_shopping/entity_config.yaml",
    )
    my_parser.add_argument(
        "--response_path", default="./Converse/bot_configs/response_template.yaml"
    )
    my_parser.add_argument(
        "--policy_path", default="./Converse/bot_configs/policy_config.yaml"
    )
    my_parser.add_argument(
        "--entity_extraction_path",
        default="./Converse/bot_configs/entity_extraction_config.yaml",
    )
    my_parser.add_argument(
        "--info_path", default="./Converse/bot_configs/dial_info_config.yaml"
    )
    my_parser.add_argument(
        "--entity_function_path", default="./Converse/bot_configs/entity_function.py"
    )
    args = my_parser.parse_args()

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
    simple_db = SimpleDB()
    simple_db.set_db("./Converse/bot_configs/online_shopping/db.yaml")

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    logging.basicConfig(filename="./converse.log", level=LOGLEVEL, format=FORMAT)

    app = Flask(
        __name__,
        static_folder=os.path.join(os.getcwd(), "Converse/demo/static"),
        template_folder=os.path.join(os.getcwd(), "Converse/demo/templates"),
    )
    app.register_blueprint(entity_service, url_prefix="/entity_service")
    app.register_blueprint(chat_window)

    # CORS(app)
    app.logger.info("Initializing Dial ...")
    app.logger.info("done!")
    app.run("0.0.0.0", port=9002, debug=True)
