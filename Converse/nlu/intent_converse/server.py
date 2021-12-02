# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


from proto import intent_pb2_grpc
from servicer import IntentServicer
from concurrent import futures
import grpc
import time
from dnnc_tinybert_inference_only import DnncIntentPredictor
import argparse


class IntentApplication:
    """
    gRPC Server for the Intent model
    """

    def __init__(self, predictor, grpc_port_number=9001, max_workers=10):
        """
        Initialize the GRPC wrapper
        :param predictor: instance of MultilingualNerBatchPredictor
        """
        self.predictor = predictor
        self.grpc_port = grpc_port_number
        self.max_workers = max_workers

    def add_servicer_to_server(self, server):
        intent_pb2_grpc.add_IntentDetectionServiceServicer_to_server(
            IntentServicer(self.predictor), server
        )

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.max_workers))
        self.add_servicer_to_server(server)
        server.add_insecure_port("[::]:" + str(self.grpc_port))
        server.start()
        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="bert-base", required=True)
    args = parser.parse_args()
    predictor = DnncIntentPredictor(model_path=args.model_path)
    grpc_application = IntentApplication(predictor=predictor)
    grpc_application.run()
