# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import os

from setuptools import Command


class Protoc(Command):
    """Build protobuf .proto files"""

    description = 'Build ".proto" (protobuf) files'
    user_options = []

    def run(self):
        print("Building protobuf files from directory:", str(os.getcwd()))

        for root, _, filenames in os.walk(""):
            for filename in filenames:
                # Compile all proto files found in directory
                if os.path.splitext(filename)[1] == ".proto":
                    path = os.path.join(root, filename)
                    self._compile_proto_if_new(path)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def _proto_is_new_or_changed(path):
        # e.g., protos/foo/bar.proto -> foo/bar
        mpath = os.path.splitext(os.path.normpath(path).split(os.sep, 1)[1])[0]
        pb2 = "{:s}_pb2.py".format(mpath)
        pb2_grpc = "{:s}_pb2_grpc.py".format(mpath)

        for target in (pb2, pb2_grpc):
            if not os.path.exists(target) or os.path.getctime(path) > os.path.getctime(
                target
            ):
                return True
            else:
                print("Protobufs already exist!")

    @staticmethod
    def _compile_proto_if_new(path):
        if Protoc._proto_is_new_or_changed(path):
            print("Compiling {:s}".format(path))
            print("Cur dir:", str(os.getcwd()))
            # This is for a cleaner requirements.txt
            from grpc_tools import protoc

            protoc.main(
                ("-I  .", "--python_out=.", "--grpc_python_out=.", "{:s}".format(path))
            )
