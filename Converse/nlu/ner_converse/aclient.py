# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import grpc

from proto import ner_pb2, ner_pb2_grpc

import json
from google.protobuf.json_format import MessageToJson


class NER:
    def __init__(self, service_channel: str):
        print("Initializing NER ... ", end="", flush=True)
        channel = grpc.insecure_channel(service_channel)

        # create a stub (client)
        self.stub = ner_pb2_grpc.NERPredictorServiceStub(channel)
        print("Done")

    def __call__(self, context, **kwargs):
        request = ner_pb2.NERPredictionRequest(
            document=bytes(context, "utf-8"), **kwargs
        )
        output = self.stub.predict(request)
        output = json.loads(MessageToJson(output))
        return output


if __name__ == "__main__":
    ner_c = NER("localhost:50051")
    utt = "i moved to san francisco from redwood city"
    print(ner_c(utt, returnSpan=True))
    utt = "my email is 123@salesforce.com"
    print(ner_c(utt, returnSpan=True))
