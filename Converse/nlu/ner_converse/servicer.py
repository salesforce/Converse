# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from proto import ner_pb2_grpc, ner_pb2


class NerServicer(ner_pb2_grpc.NERPredictorServiceServicer):
    def __init__(self, batch_predictor):
        super(NerServicer, self).__init__()
        self.predictor = batch_predictor

    def predict(self, request, context):
        try:
            text = request.document.decode("utf-8")
            response = self.predictor.predict(text, request.returnSpan)
        except Exception as e:
            response = ner_pb2.NERPredictionResponse()
            response.success = False
            response.error = str(e)
        return response
