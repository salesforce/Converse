# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import transformers
import torch
import torch.nn.functional as F
import torch.nn as nn
import os
from proto import ner_pb2
import logging

logger = logging.getLogger(__name__)


class NerAddrParser(transformers.BertPreTrainedModel):
    def __init__(self, config, num_labels_ner, num_labels_addr):
        super(NerAddrParser, self).__init__(config)
        self.num_labels_ner = num_labels_ner
        self.num_labels_addr = num_labels_addr

        self.bert = transformers.BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier_ner = nn.Linear(config.hidden_size, self.num_labels_ner)
        self.classifier_addr = nn.Linear(config.hidden_size, self.num_labels_addr)

        self.init_weights()

    def forward(
        self,
        input_ids,
        attention_mask=None,
        token_type_ids=None,
        position_ids=None,
        head_mask=None,
    ):
        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)
        logits_ner = self.classifier_ner(sequence_output)
        logits_addr = self.classifier_addr(sequence_output)

        return logits_ner, logits_addr


class NerPredictor:
    def __init__(self, model_path="./model/tinybert_6l"):
        self.max_seq_length = 128
        self.per_gpu_eval_batch_size = 64
        self.do_lower_case = True

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.n_gpu = torch.cuda.device_count()

        model_path = os.path.abspath(model_path)
        model_config = torch.load(
            model_path + "/config.pt", map_location=lambda storage, loc: storage
        )

        self.model = NerAddrParser.from_pretrained(
            model_path,
            num_labels_ner=model_config["num_tags_ner"],
            num_labels_addr=model_config["num_tags_addr"],
        )
        self.model.to(self.device)
        self.model.eval()

        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            model_path, do_lower_case=True
        )

        self.id2tag = model_config["id2tag_ner"]
        self.id2tag_addr = model_config["id2tag_addr"]
        self.session_id = 0
        self.mask_id = model_config["mask_id"]
        self.cls_id = self.tokenizer.cls_token_id
        self.sep_id = self.tokenizer.sep_token_id

        self.logger = logging.getLogger(__name__)

    def text2id(self, text):
        tokens = self.tokenizer.tokenize(text)
        token_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        ## to mitigate some dark operations by the bert tokenizer
        ## 1. some tokens in the original text may be erased in the tokenizeration
        ## 2. some word may be splitted before feeding to the wordpiece tokenization.
        ## in such a way the second subtoken won't have ## as prefix.
        ## this causes issues of the character span calculation
        ## the function below aligns the tokens from the bert tokenizer to the original text
        ## token_starts is a list of the starting index in the original text for each token
        ## token_ends is a list of the ending index for each token
        ## the index is character level so that we do not need to recompute in the span calculation.
        token_starts, token_ends = self.token_align(tokens, text.lower())
        return text, token_ids, token_starts, token_ends

    def token_align(self, tokens, text):
        ### two pointer problem
        ## pointer p1 points to the tokens
        ## pointer p2 points to words
        words = text.split(" ")
        token_starts = []
        token_ends = []
        p1, p2, cp = 0, 0, 0
        l1, l2 = len(tokens), len(words)
        ## sub_offset is to deal with the subword offset inside a word
        ## for example _ORC_
        ## when match '_' to '_ORC_' for a second time, we need to search from position 1
        ## to prevent double counting
        sub_offset = 0
        while p1 < l1 and p2 < l2:
            token = tokens[p1]
            word_cur = words[p2]

            ## edge case handler for the [UNK] token
            if token == "[UNK]":
                token_starts.append(cp)
                token_ends.append(
                    None
                )  ##for [UNK] token, we do not know where it ends unless there is a nother matched token afterwards
                p1 += 1
                sub_offset = 0
                continue

            if token.startswith("##"):
                token = token[2:]

            if token == word_cur:
                token_starts.append(cp)
                token_ends.append(cp + len(token))
                p1 += 1
                p2 += 1
                cp += len(token) + 1
                sub_offset = 0
            else:
                start = word_cur.find(token, sub_offset)
                if start == -1:
                    p2 += 1
                    cp += len(word_cur) + 1
                    sub_offset = 0
                else:
                    token_starts.append(cp + start)
                    token_ends.append(token_starts[-1] + len(token))
                    p1 += 1
                    sub_offset = start + len(token)

        # if the last token is [UNK] then feed the lens of the text as the token_end
        if token_ends and token_ends[-1] is None:
            token_ends[-1] = len(text)

        return token_starts, token_ends

    def tag_entities(self, token_ids: torch.LongTensor, masks: torch.LongTensor):
        with torch.no_grad():
            token_ids = token_ids.to(self.device)
            masks = masks.to(self.device)
            logits, logits_addr = self.model(
                token_ids, token_type_ids=None, attention_mask=masks
            )
            logits = logits[:, 1:, :]
            logits_addr = logits_addr[:, 1:, :]
            scores = F.softmax(logits, dim=2)
            scores_addr = F.softmax(logits_addr, dim=2)

        probs, preds = torch.max(scores, 2)
        probs_addr, preds_addr = torch.max(scores_addr, 2)

        return probs.tolist(), preds.tolist(), probs_addr.tolist(), preds_addr.tolist()

    def generate_entity(
        self,
        text: str,
        tag: str,
        probability: float,
        start: int,
        end: int,
        return_span: bool,
    ):
        pred = ner_pb2.NERPredictions()
        pred.label = tag
        pred.probability = probability
        pred.token = text[start:end]
        if return_span:
            pred.span.start = start
            pred.span.end = end
        return pred

    # @staticmethod
    def generate_entity_addr(
        self,
        text: str,
        tag_cache: list,
        probability: float,
        start_cache: list,
        end_cache: list,
        return_span: bool,
    ):
        pred = ner_pb2.NERPredictions()
        pred.label = "AP/LOCATION"
        pred.probability = probability
        pred.token = text[start_cache[0] : end_cache[-1]]
        address_line = [
            tag + ":" + text[start:end]
            for start, end, tag in zip(start_cache, end_cache, tag_cache)
        ]
        pred.normalizedValue = "|".join(address_line)
        if return_span:
            pred.span.start = start_cache[0]
            pred.span.end = end_cache[-1]
        return pred

    @staticmethod
    def is_entity(tag_prev, tag_cur):
        token_change = tag_cur != tag_prev
        return (
            token_change and (tag_cur != "O"),
            token_change and (tag_prev != "O") and (tag_prev is not None),
        )

    def decode_entities(
        self, text, token_starts, token_ends, preds, probabilities, return_span
    ):
        tags = [self.id2tag[x] for x in preds]
        predictions = []
        start_idx, end_idx = -1, -1
        tag_prev, prob_prev = None, None
        for token_start, token_end, tag, prob in zip(
            token_starts, token_ends, tags, probabilities
        ):
            # token = text[token_start:token_end]
            if "-" in tag:
                tag = tag.split("-")[1]
            elif "_" in tag:
                tag = tag.split("_")[1]

            # if token.startswith('##'):
            #     end_idx = token_end
            #     continue
            if token_start == end_idx:
                tag = tag_prev

            is_begin, is_end = self.is_entity(tag_prev, tag)

            # note there are cases when both is_begin and is_end are true. For example, LOC, LOC, DATE.
            # In this case DATE is both the end of the previous entity and the beginning of the current entity
            # In this case is_end has to be processed first
            if is_end:
                if end_idx is None:  ## take care of [UNK] tokens
                    end_idx = token_start
                entity = self.generate_entity(
                    text=text,
                    tag=tag_prev,
                    probability=prob_prev,
                    start=start_idx,
                    end=end_idx,
                    return_span=return_span,
                )
                predictions.append(entity)
                tag_prev, prob_prev = None, None

            if is_begin:
                tag_prev, prob_prev, start_idx = tag, prob, token_start

            end_idx = token_end

        # check if there is any entity in the cache. if so record it
        if tag_prev is not None:
            if end_idx is None:  ## take care of [UNK] tokens
                end_idx = token_start
            entity = self.generate_entity(
                text=text,
                tag=tag_prev,
                probability=prob_prev,
                start=start_idx,
                end=end_idx,
                return_span=return_span,
            )
            predictions.append(entity)

        return predictions

    def decode_entities_addr(
        self, text, token_starts, token_ends, preds_addr, probabilities, return_span
    ):
        tags = [
            self.id2tag_addr[x] if "Recipient" not in self.id2tag_addr[x] else "O"
            for x in preds_addr
        ]  ## remove the recipient tag detected by the address parser
        predictions = []
        tags_cache, start_idx_cache, end_idx_cache, probs_cache, token_prev = (
            [],
            [],
            [],
            1.0,
            None,
        )
        start_idx, end_idx = -1, -1
        tag_prev, prob_prev = None, None
        for token_start, token_end, tag, prob in zip(
            token_starts, token_ends, tags, probabilities
        ):
            if "-" in tag:
                tag = tag.split("-")[1]
            elif "_" in tag:
                tag = tag.split("_")[1]

            if token_start == end_idx:
                tag = tag_prev

            is_begin, is_end = self.is_entity(tag_prev, tag)

            # note there are cases when both is_begin and is_end are true. For example, LOC, LOC, DATE.
            # In this case DATE is both the end of the previous entity and the beginning of the current entity
            # In this case is_end has to be processed first
            if is_end:
                if end_idx is None:  ## take care of [UNK] tokens
                    end_idx = token_start

                if (
                    (not end_idx_cache)
                    or (start_idx == end_idx_cache[-1] + 1)
                    or (token_prev == ",")
                ):
                    tags_cache.append(tag_prev)
                    start_idx_cache.append(start_idx)
                    end_idx_cache.append(end_idx)
                    probs_cache *= prob_prev
                else:
                    entity = self.generate_entity_addr(
                        text=text,
                        tag_cache=tags_cache,
                        probability=probs_cache,
                        start_cache=start_idx_cache,
                        end_cache=end_idx_cache,
                        return_span=return_span,
                    )
                    tags_cache, start_idx_cache, end_idx_cache, probs_cache = (
                        [tag],
                        [start_idx],
                        [end_idx],
                        prob_prev,
                    )
                    predictions.append(entity)
                tag_prev, prob_prev = None, None

            if is_begin:
                tag_prev, prob_prev, start_idx = tag, prob, token_start

            end_idx = token_end
            token_prev = text[token_start:token_end]

        # check if there is any entity in the cache. if so record it
        if tag_prev is not None:
            if end_idx is None:  ## take care of [UNK] tokens
                end_idx = token_start
            if (not end_idx_cache) or (start_idx == end_idx_cache[-1] + 1):
                tags_cache.append(tag_prev)
                start_idx_cache.append(start_idx)
                end_idx_cache.append(end_idx)
                probs_cache *= prob_prev
            if tags_cache:
                entity = self.generate_entity_addr(
                    text=text,
                    tag_cache=tags_cache,
                    probability=probs_cache,
                    start_cache=start_idx_cache,
                    end_cache=end_idx_cache,
                    return_span=return_span,
                )
                predictions.append(entity)

        return predictions

    def produce_response(self, params):
        (
            text,
            token_starts,
            token_ends,
            probs,
            preds,
            return_span,
            probs_addr,
            preds_addr,
        ) = params
        try:
            response_ner = self.decode_entities(
                text, token_starts, token_ends, preds, probs, return_span
            )
            response_addr = self.decode_entities_addr(
                text, token_starts, token_ends, preds_addr, probs_addr, return_span
            )

            response = ner_pb2.NERPredictionResponse()
            response.success = True
            response.probabilities.extend(response_ner)
            response.probabilities.extend(response_addr)

            return response
        except Exception as e:
            self.logger.exception(
                "Exception occurred: unexpected behaviour while formatting the NER response."
            )
            response = ner_pb2.NERPredictionResponse()
            response.success = False
            response.error = str(e)
            return response

    def predict(self, text, return_span=True):
        batch_id = []
        batch_token_starts = []
        batch_token_ends = []
        batch_text = []
        dynamic_batch_seq_len = 0
        batch_seq_len = []
        batch_span = []

        text, token_ids, token_starts, token_ends = self.text2id(text)
        batch_text.append(text)
        batch_id.append([self.cls_id] + token_ids + [self.sep_id])
        batch_token_starts.append(token_starts)
        batch_token_ends.append(token_ends)
        batch_span.append(return_span)
        # Update dynamic batch size
        tokens_len = len(token_ids)
        batch_seq_len.append(tokens_len)
        if tokens_len + 2 > dynamic_batch_seq_len:
            dynamic_batch_seq_len = tokens_len + 2

        batch_mask = []
        # Padding & generate masks
        for utterance_len, token_id in zip(batch_seq_len, batch_id):
            utterance_len += 2
            # token_id = [self.cls_id] + token_id + [self.sep_id]
            token_id += [
                self.mask_id for _ in range(dynamic_batch_seq_len - utterance_len)
            ]
            batch_mask.append(
                [
                    1 if idx < utterance_len else 0
                    for idx in range(dynamic_batch_seq_len)
                ]
            )

        batch_id = torch.LongTensor(batch_id)
        batch_mask = torch.LongTensor(batch_mask)

        # Calls the model on GPU/CPU
        (
            batch_probs,
            batch_preds,
            batch_probs_addr,
            batch_preds_addr,
        ) = self.tag_entities(batch_id, batch_mask)

        text = batch_text[0]
        token_starts = batch_token_starts[0]
        token_ends = batch_token_ends[0]
        token_length = len(token_starts)

        return self.produce_response(
            (
                text,
                token_starts,
                token_ends,
                batch_probs[0][:token_length],
                batch_preds[0][:token_length],
                batch_span[0],
                batch_probs_addr[0][:token_length],
                batch_preds_addr[0][:token_length],
            )
        )


if __name__ == "__main__":
    ner = NerPredictor()
    print(ner.predict("i love New York"))
