#!/bin/bash

export PYTHONPATH=./

INTENT_MODEL_PATH=$1
NER_MODEL_PATH=$2

python -u Converse/nlu/intent_converse/server.py --model_path $INTENT_MODEL_PATH >server_intent.out &

python -u Converse/nlu/ner_converse/server.py --model_path $NER_MODEL_PATH >server_ner_addr.out &
python -u Converse/nlu/ner_converse/aggr_server.py >server_ner.out
