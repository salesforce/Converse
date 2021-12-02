# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


import torch
from TinyBERT.transformer.tokenization import BertTokenizer
from TinyBERT.transformer.modeling import TinyBertForSequenceClassification

from utils import truncate_seq_pair
from utils import InputExample, InputFeatures
from utils import get_logger

ENTAILMENT = "entailment"
NON_ENTAILMENT = "non_entailment"

logger = get_logger(__name__)


class DNNC:
    def __init__(self, path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.max_seq_length = 128

        self.label_list = [ENTAILMENT, NON_ENTAILMENT]
        self.num_labels = len(self.label_list)

        self.do_lower_case = True

        self.tokenizer = BertTokenizer.from_pretrained(path, do_lower_case=True)
        self.tokenizer.cls_token = "[CLS]"
        self.tokenizer.sep_token = "[SEP]"

        self.model = TinyBertForSequenceClassification.from_pretrained(
            path, num_labels=self.num_labels
        )
        self.model.to(self.device)

    def convert_examples_to_features(self, examples, train):
        label_map = {label: i for i, label in enumerate(self.label_list)}

        if train:
            label_distribution = torch.FloatTensor(len(label_map)).zero_()
        else:
            label_distribution = None

        features = []
        for (ex_index, example) in enumerate(examples):
            tokens_a = self.tokenizer.tokenize(example.text_a)
            tokens_b = self.tokenizer.tokenize(example.text_b)

            truncate_seq_pair(tokens_a, tokens_b, self.max_seq_length - 3)

            tokens = [self.tokenizer.cls_token] + tokens_a + [self.tokenizer.sep_token]
            segment_ids = [0] * len(tokens)

            tokens_b = tokens_b + [self.tokenizer.sep_token]
            segment_ids += [1] * len(tokens_b)
            tokens += tokens_b

            input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
            input_mask = [1] * len(input_ids)

            padding = [0] * (self.max_seq_length - len(input_ids))
            input_ids += padding
            input_mask += padding
            segment_ids += padding

            assert len(input_ids) == self.max_seq_length
            assert len(input_mask) == self.max_seq_length
            assert len(segment_ids) == self.max_seq_length

            if example.label is None:
                label_id = -1
            else:
                label_id = label_map[example.label]

            if train:
                label_distribution[label_id] += 1.0

            features.append(
                InputFeatures(
                    input_ids=input_ids,
                    input_mask=input_mask,
                    segment_ids=segment_ids,
                    label_id=label_id,
                )
            )

        if train:
            label_distribution = label_distribution / label_distribution.sum()
            return features, label_distribution
        else:
            return features

    def predict(self, data):

        self.model.eval()

        input = [InputExample(premise, hypothesis) for (premise, hypothesis) in data]

        eval_features = self.convert_examples_to_features(input, train=False)
        input_ids = torch.tensor([f.input_ids for f in eval_features], dtype=torch.long)
        input_mask = torch.tensor(
            [f.input_mask for f in eval_features], dtype=torch.long
        )
        segment_ids = torch.tensor(
            [f.segment_ids for f in eval_features], dtype=torch.long
        )

        max_len = input_mask.sum(dim=1).max().item()
        input_ids = input_ids[:, :max_len]
        input_mask = input_mask[:, :max_len]
        segment_ids = segment_ids[:, :max_len]

        CHUNK = 500
        EXAMPLE_NUM = input_ids.size(0)
        labels = []
        probs = None
        start_index = 0

        while start_index < EXAMPLE_NUM:
            end_index = min(start_index + CHUNK, EXAMPLE_NUM)

            input_ids_ = input_ids[start_index:end_index, :].to(self.device)
            input_mask_ = input_mask[start_index:end_index, :].to(self.device)
            segment_ids_ = segment_ids[start_index:end_index, :].to(self.device)

            with torch.no_grad():
                outputs = self.model(
                    input_ids=input_ids_,
                    attention_mask=input_mask_,
                    token_type_ids=segment_ids_,
                )
                logits = outputs[0]
                probs_ = torch.softmax(logits, dim=1)

            probs_ = probs_.detach().cpu()
            if probs is None:
                probs = probs_
            else:
                probs = torch.cat((probs, probs_), dim=0)
            labels += [
                self.label_list[torch.max(probs_[i], dim=0)[1].item()]
                for i in range(probs_.size(0))
            ]
            start_index = end_index

        assert len(labels) == EXAMPLE_NUM
        assert probs.size(0) == EXAMPLE_NUM

        return labels, probs


class DnncIntentPredictor:
    def __init__(self, model_path):
        self.model = DNNC(path=model_path)

    def predict(
        self,
        input: str,
        tasks=None,
        task_key="task",
        example_key="examples",
        threshold=0.65,
    ):

        input = input.lower()

        nli_input = []
        for t in tasks:
            for e in t[example_key]:
                nli_input.append((input, e.lower()))

        assert len(nli_input) > 0

        results = self.model.predict(nli_input)
        maxScore, maxIndex = results[1][:, 0].max(dim=0)

        maxScore = maxScore.item()
        maxIndex = maxIndex.item()

        intent = "None"
        matched_example = "None"
        if maxScore < threshold:
            return intent, 0, matched_example
        else:
            index = -1
            for t in tasks:
                for e in t[example_key]:
                    index += 1
                    if index == maxIndex:
                        intent = t[task_key]
                        matched_example = e
            return intent, maxScore, matched_example
