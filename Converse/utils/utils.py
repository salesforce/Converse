# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from nltk import edit_distance
from collections import defaultdict
import requests
import json


def wer(asr, true):
    return edit_distance(asr, true) / len(true)


def get_dict_key(dic: dict):
    """
    return the dictionary key
    the dictionary must contain only a single entry
    """
    assert len(dic) == 1
    return list(dic.keys())[0]


def combine_entity_words_into_span(words, nes):
    # combine words of same ner type into span
    spans = defaultdict(list)
    prev_tag = ""
    span = ""
    for word, tag in zip(words, nes):
        if tag == prev_tag:
            span = span + " " + word
        else:
            if prev_tag != "" and prev_tag != "O":
                spans[prev_tag].append(span)
            span = word
        prev_tag = tag
    if prev_tag != "" and prev_tag != "O":
        spans[prev_tag].append(span)
    # for loc
    loc = None
    if "CARDINAL" in spans and "FAC" in spans and "LOC" in spans:
        loc = (
            " ".join(spans["CARDINAL"])
            + " "
            + " ".join(spans["FAC"])
            + " "
            + " ".join(spans["LOC"])
        )
        del spans["CARDINAL"]
        del spans["FAC"]
        del spans["LOC"]
    elif "CARDINAL" in spans and "FAC" in spans:
        loc = " ".join(spans["CARDINAL"]) + " " + " ".join(spans["FAC"])
        del spans["CARDINAL"]
        del spans["FAC"]
    elif "FAC" in spans and "LOC" in spans:
        loc = " ".join(spans["FAC"]) + " " + " ".join(spans["LOC"])
        del spans["FAC"]
        del spans["LOC"]
    if loc:
        spans["LOC"] = [loc]
    return spans


def entity_api_call(url, entities, *argv, **kargs):
    json_message = {
        "entities": entities,
        "cur_task": kargs["cur_task"],
        "cur_entity": kargs["cur_entity_name"],
    }
    r = requests.post(url, json=json_message)
    if r.status_code != 200:
        return {"success": False, "msg": "ERROR!"}
    return r.json()


def resp(success: bool, msg: str):
    return {"success": success, "msg": msg}


def json_resp(success: bool, msg: str):
    return json.dumps({"success": success, "msg": msg})
