# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from proto import intent_pb2
from proto import intent_pb2_grpc


class IntentServicer(intent_pb2_grpc.IntentDetectionServiceServicer):
    def __init__(self, predictor):
        super(IntentServicer, self).__init__()
        self.predictor = predictor

    def IntentDetection(self, request, context):
        try:
            text = request.document
            tasks_list = []
            for t in request.tasks:
                sample_list = []
                for s in t.samples:
                    sample_list.append(s)
                tasks_list.append({"task": t.label, "examples": sample_list})
            intent, max_score, sent = self.predictor.predict(text, tasks_list)
            response = intent_pb2.IntentDetectionResponse()
            if intent == "None":
                response.results.success = False
            else:
                response.results.success = True
                response.results.label = intent
                response.results.probability = max_score
                response.results.sent = sent

        except Exception as e:
            response = intent_pb2.IntentDetectionResponse()
            response.results.success = False
            response.results.label = "None"
            response.results.probability = 0
            response.results.sent = str(e)

        return response
