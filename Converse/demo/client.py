# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import requests
import sys
import uuid
import time


def process_call(cid, text):
    r = requests.post("http://0.0.0.0:9002/process", json={"cid": cid, "text": text})
    if r.status_code != 200:
        return {"response": "ERROR"}
    return r.json()


def reset_call(cid):
    r = requests.post("http://0.0.0.0:9002/reset", json={"cid": cid})
    if r.status_code != 200:
        return {"response": "ERROR"}
    return r.json()


def cur_entity_call():
    r = requests.post("http://0.0.0.0:9002/cur_entity")
    if r.status_code != 200:
        return {"response": "ERROR"}
    return r.json()


if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
    print(f"you conversation id is {cid}")
    res = reset_call(cid)["response"]
    print("Agent:", res)
    while True:
        sent = input("User:  ")
        # print(cur_entity_call()) # for ASR lm setting
        if sent == "RESET":
            res = reset_call(cid)["response"]
            print("Agent:", res)
        else:
            res = process_call(cid, sent)["response"]
            res_wait = res.split("<wait>")  # mimic clicking authenticator
            if len(res_wait) > 1:  # hack
                print("Agent:", res_wait[0].strip())
                time.sleep(int(res_wait[1]))
                if len(res_wait) == 3:
                    print("Agent:", res_wait[2].strip())
            else:
                print("Agent:", res)
