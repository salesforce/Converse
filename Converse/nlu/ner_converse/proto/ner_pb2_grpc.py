# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import ner_pb2 as ner_pb2


class NERPredictorServiceStub(object):
    """
    Named Entity Recognition Predictor Service definition, accepts a model_id & document and returns labels with
    probabilities for each.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.predict = channel.unary_unary(
            "/NERPredictorService/predict",
            request_serializer=ner_pb2.NERPredictionRequest.SerializeToString,
            response_deserializer=ner_pb2.NERPredictionResponse.FromString,
        )


class NERPredictorServiceServicer(object):
    """
    Named Entity Recognition Predictor Service definition, accepts a model_id & document and returns labels with
    probabilities for each.
    """

    def predict(self, request, context):
        # missing associated documentation comment in .proto file
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_NERPredictorServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "predict": grpc.unary_unary_rpc_method_handler(
            servicer.predict,
            request_deserializer=ner_pb2.NERPredictionRequest.FromString,
            response_serializer=ner_pb2.NERPredictionResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "NERPredictorService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
