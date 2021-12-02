# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging
import os

from flask import Flask, request
from flask_cors import CORS

from Converse.simple_db.simple_db import SimpleDB

import requests
from wrapt_timeout_decorator import timeout
from Converse.utils.utils import json_resp


app = Flask(__name__, template_folder="./")
if os.environ.get("WSGI", "") == "gunicorn":
    # to run with gunicorn e.g.
    # WSGI=gunicorn gunicorn service_backend:app \
    # --bind=0.0.0.0:8001 --workers=2 \
    # --access-logfile /tmp/log/demo/access.log \
    # --error-logfile /tmp/log/demo/error.log \
    # --log-level=[debug|info|warning|error|critical]
    logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
else:
    # or run without gunicorn e.g.
    # LOGLEVEL=[debug|info|warning|error|critical] \
    # python ./dial_backend.py
    LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    logging.basicConfig(filename="../../converse.log", level=LOGLEVEL, format=FORMAT)

CORS(app)


# There are several APIs modified from the functions in entity_functions.py .
# These APIs are examples for the entity services.


@timeout(0.1)
@app.route("/inch_2_cm", methods=["POST"])
def funcInch2Cm():
    dm_msg = request.json["entities"]
    entity_name = "inch"
    inch = float(dm_msg[entity_name])
    cm = 2.54 * inch
    return json_resp(True, "{} inch equals to {} centimeter".format(inch, cm))


@timeout(1.0)
@app.route("/get_weather", methods=["POST"])
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
            True, "Weather condition is {} at {}, {}".format(res[0], res[1], zipcode)
        )
    except Exception:
        return json_resp(
            False, msg="Weather condition not availiable at {}".format(zipcode)
        )


@timeout(0.1)
@app.route("/get_tv_plan", methods=["POST"])
def funcGetTVPlanPrice():
    dm_msg = request.json["entities"]
    entity_name = "new_tv_plan"
    tvplan = dm_msg[entity_name]
    price = {"hulu live": 200, "hulu tv": 200, "fubo tv": 300, "pluto tv": 500}
    try:
        return json_resp(
            True, "the price of {} is {} dollar per year".format(tvplan, price[tvplan])
        )
    except Exception:
        return json_resp(False, msg="the price of {} is not avaiable".format(tvplan))


@timeout(0.5)
@app.route("/single_step_verify", methods=["POST"])
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
@app.route("/get_order_status", methods=["POST"])
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
@app.route("/query_order", methods=["POST"])
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
@app.route("/add_more_to_order", methods=["POST"])
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


def run():
    app.logger.info("Initializing Dial ...")
    app.logger.info("done!")
    app.run("localhost", port=8001)


@app.route("/testdb", methods=["GET"])
def test_db():
    res = simple_db.test_db()
    return json_resp(False, msg=f"{res}")


if __name__ == "__main__":
    simple_db = SimpleDB()
    simple_db.set_db("./Converse/bot_configs/online_shopping/db.yaml")
    run()
