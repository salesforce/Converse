#!/bin/bash
python -u server.py --model_path ./models/tinybert_ner >server_ner_addr.out &
python -u aggr_server.py >server_ner.out 
