# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from proto import ner_pb2_grpc
from servicer import NerServicer
from concurrent import futures
import grpc
import time
import logging
import argparse
from tinybert_ner import NerPredictor

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.WARN,
)

logger = logging.getLogger(__name__)

class NERApplication:
    """
    gRPC Server for the Intent model
    """

    def __init__(self, predictor, grpc_port_number=8090, max_workers=10):
        """
        Initialize the GRPC wrapper
        :param predictor: instance of MultilingualNerBatchPredictor
        """
        self.predictor = predictor
        self.grpc_port = grpc_port_number
        self.max_workers = max_workers

    def add_servicer_to_server(self, server):
        ner_pb2_grpc.add_NERPredictorServiceServicer_to_server(
            NerServicer(self.predictor), server
        )

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.max_workers))
        self.add_servicer_to_server(server)
        server.add_insecure_port("[::]:" + str(self.grpc_port))
        server.start()
        print("Starting server. Listening on port " + str(self.grpc_port))
        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_path", type=str, default="./models/tinybert_6l", required=False
    )
    args = parser.parse_args()

    predictor = NerPredictor(model_path=args.model_path)
    logger.info("NER server is running on port {}.".format(8090))
    grpc_application = NERApplication(predictor=predictor)
    grpc_application.run()
