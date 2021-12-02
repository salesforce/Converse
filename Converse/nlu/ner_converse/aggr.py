# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import grpc

# import the generated classes
from proto import ner_pb2
from proto import ner_pb2_grpc
from concurrent import futures

import duckling


class Aggregator(object):
    def __init__(self, ner_port="0.0.0.0:8090", max_workers=8):
        self.duckling_entities = [
            "amount-of-money",
            "email",
            "number",
            "ordinal",
            "phone-number",
            "time",
            "url",
        ]
        self.ner_port = ner_port
        self.max_workers = max_workers
        # open a gRPC channel
        self.channel = grpc.insecure_channel(self.ner_port)
        # create a stub (client)
        self.stub = ner_pb2_grpc.NERPredictorServiceStub(self.channel)
        self.executor = futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.dk = duckling.Duckling()
        self.dk.load()
        self.services = [self.ner_parse, self.duckling_parse]
        self.date_time_labels = {"DATE", "TIME", "DUCKLING/time"}
        self.date_time_white_list = ""

    def parse(self, query):
        responses_future = [
            self.executor.submit(service, query) for service in self.services
        ]
        responses = {}
        for response_future in futures.as_completed(responses_future):
            response = response_future.result()
            responses[response[0]] = response[1]
        return self.post_proc(responses)

    def post_proc(self, responses):
        responses["DK"] = [
            response
            for response in responses["DK"]
            if (
                response.label in self.date_time_labels
                and response.token in self.date_time_white_list
            )
            or (response.label not in self.date_time_labels)
        ]
        self.date_time_white_list = ""
        response_final = ner_pb2.NERPredictionResponse()
        response_final.success = True
        for service_name, response in responses.items():
            response_final.probabilities.extend(response)
        return response_final

    def ner_parse(self, query):
        ner_request = ner_pb2.NERPredictionRequest(
            document=bytes(query, "utf-8"), returnSpan=True
        )
        response = self.stub.predict(ner_request)
        for probability in response.probabilities:
            if probability.label in self.date_time_labels:
                self.date_time_white_list += probability.token
        return "NER", response.probabilities

    def duckling_parse(self, query):
        results = self.dk.parse(query)
        entities = []
        for result in results:
            if "value" not in result:
                continue
            if "value" not in result["value"]:
                continue
            if result["dim"] in self.duckling_entities:
                entity = ner_pb2.NERPredictions()
                entity.label = "DUCKLING/" + result["dim"]
                entity.token = result["body"]
                if result["dim"] == "amount-of-money" and "unit" in result["value"]:
                    entity.normalizedValue = (
                        f"value:{result['value']['value']}"
                        f"|unit:{result['value']['unit']}"
                    )
                else:
                    entity.normalizedValue = str(result["value"]["value"])
                entity.span.start = result["start"]
                entity.span.end = result["end"]
                entities.append(entity)
        return "DK", entities
