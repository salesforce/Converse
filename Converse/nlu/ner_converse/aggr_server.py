# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import logging

import sys
import time
import grpc

# import the generated classes
from proto import ner_pb2
from proto import ner_pb2_grpc

from aggr import Aggregator
from concurrent import futures


logging.basicConfig(
    format="%(process)d-%(levelname)s-%(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class AggregatorServiceServicer(ner_pb2_grpc.NERPredictorServiceServicer):
    def __init__(self, aggregator):
        super(AggregatorServiceServicer, self).__init__()
        self.aggregator = aggregator

    def predict(self, request, context):
        try:
            text = request.document.decode("utf-8")
            response = self.aggregator.parse(text)
        except Exception as e:
            response = ner_pb2.NERPredictionResponse()
            response.success = False
            response.error = str(e)
        return response


if __name__ == "__main__":
    aggr = Aggregator(ner_port="0.0.0.0:8090")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ner_pb2_grpc.add_NERPredictorServiceServicer_to_server(
        AggregatorServiceServicer(aggregator=aggr), server
    )
    print("Starting server. Listening on port 50051.")
    server.add_insecure_port("[::]:50051")
    server.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
