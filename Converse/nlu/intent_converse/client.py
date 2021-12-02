# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import grpc

import Converse.nlu.intent_converse.proto.intent_pb2 as intent_pb2
import Converse.nlu.intent_converse.proto.intent_pb2_grpc as intent_pb2_grpc
from Converse.config.task_config import TaskConfig, FAQConfig


class IntentDetection:
    def __init__(
        self,
        task_config: TaskConfig,
        service_channel: str,
        faq_config: FAQConfig = None,
    ):
        print("Initializing IntentDetection ... ", end="", flush=True)
        self.request_wo_doc = self.intent_samples(task_config, faq_config)

        # Open a gRPC channel
        channel = grpc.insecure_channel(service_channel)

        # Create a stub (client)
        self.stub = intent_pb2_grpc.IntentDetectionServiceStub(channel)
        print("Done")

    def intent_samples(self, task_config: TaskConfig, faq_config: FAQConfig = None):
        """ Transfer samples into IntentDetectionRequest """
        request = intent_pb2.IntentDetectionRequest()
        c = []
        for task in task_config:
            t = intent_pb2.IntentClass()
            t.label = task
            t.samples.extend(task_config[task].samples)
            c.append(t)
        request.tasks.extend(c)
        if faq_config:
            c_faq = []
            for faq in faq_config:
                if "nli" in faq_config[faq].question_match_options:
                    t = intent_pb2.IntentClass()
                    t.label = faq
                    t.samples.extend(faq_config[faq].samples)
                    c_faq.append(t)
            request.tasks.extend(c_faq)

        return request

    def __call__(self, text: str) -> dict:
        """ Return intent detection results """
        req = self.request_wo_doc
        # print(req)
        req.document = text

        # Make the call
        response = self.stub.IntentDetection(req)
        success = response.results.success
        intent = response.results.label
        prob = response.results.probability
        sent = response.results.sent

        return {"success": success, "intent": intent, "prob": prob, "sent": sent}


if __name__ == "__main__":
    client = IntentDetection(
        TaskConfig("./Converse/bot_configs/online_shopping/tasks.yaml"), "localhost:9001"
    )
    utt = "the account number"
    result = client(utt)
    print(result)
    utt = "check order status."
    result = client(utt)
    print(result)
    while True:
        utt = input("User:")
        result = client(utt)
        print(result)
