# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import torch

from pytorch_pretrained_bert.tokenization import BertTokenizer
from pytorch_pretrained_bert.modeling import BertForSequenceClassification


class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text_a, text_b=None, label=None):
        """Constructs a InputExample.

        Args:
            guid: Unique id for the example.
            text_a: string. The untokenized text of the first sequence. For single
            sequence tasks, only this sequence must be specified.
            text_b: (Optional) string. The untokenized text of the second sequence.
            Only must be specified for sequence pair tasks.
            label: (Optional) string. The label of the example. This should be
            specified for train and dev examples, but not for test examples.
        """
        self.guid = guid
        self.text_a = text_a
        self.text_b = text_b
        self.label = label


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, input_mask, segment_ids, label_id):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_id = label_id


def convert_examples_to_features(examples, label_list, max_seq_length, tokenizer):
    """Loads a data file into a list of `InputBatch`s."""

    label_map = {label: i for i, label in enumerate(label_list)}

    features = []
    for (ex_index, example) in enumerate(examples):
        tokens_a = tokenizer.tokenize(example.text_a)

        tokens_b = None
        if example.text_b:
            tokens_b = tokenizer.tokenize(example.text_b)
            # Modifies `tokens_a` and `tokens_b` in place so that the total
            # length is less than the specified length.
            # Account for [CLS], [SEP], [SEP] with "- 3"
            _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
        else:
            # Account for [CLS] and [SEP] with "- 2"
            if len(tokens_a) > max_seq_length - 2:
                tokens_a = tokens_a[: (max_seq_length - 2)]

        # The convention in BERT is:
        # (a) For sequence pairs:
        #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
        #  type_ids: 0   0  0    0    0     0       0 0    1  1  1  1   1 1
        # (b) For single sequences:
        #  tokens:   [CLS] the dog is hairy . [SEP]
        #  type_ids: 0   0   0   0  0     0 0
        #
        # Where "type_ids" are used to indicate whether this is the first
        # sequence or the second sequence. The embedding vectors for `type=0` and
        # `type=1` were learned during pre-training and are added to the wordpiece
        # embedding vector (and position vector). This is not *strictly* necessary
        # since the [SEP] token unambiguously separates the sequences, but it makes
        # it easier for the model to learn the concept of sequences.
        #
        # For classification tasks, the first vector (corresponding to [CLS]) is
        # used as as the "sentence vector". Note that this only makes sense because
        # the entire model is fine-tuned.
        tokens = ["[CLS]"] + tokens_a + ["[SEP]"]
        segment_ids = [0] * len(tokens)

        if tokens_b:
            tokens += tokens_b + ["[SEP]"]
            segment_ids += [1] * (len(tokens_b) + 1)

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        input_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        padding = [0] * (max_seq_length - len(input_ids))
        input_ids += padding
        input_mask += padding
        segment_ids += padding

        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length

        label_id = None

        features.append(
            InputFeatures(
                input_ids=input_ids,
                input_mask=input_mask,
                segment_ids=segment_ids,
                label_id=label_id,
            )
        )
    return features


def _truncate_seq_pair(tokens_a, tokens_b, max_length):
    """Truncates a sequence pair in place to the maximum length."""

    # This is a simple heuristic which will always truncate the longer sequence
    # one token at a time. This makes more sense than truncating an equal percent
    # of tokens from each, since if one sequence is very short then each token
    # that's truncated likely contains more information than a longer sequence.
    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_length:
            break
        if len(tokens_a) > len(tokens_b):
            tokens_a.pop()
        else:
            tokens_b.pop()


class BertNliPredictor:
    def __init__(
        self,
        # bert_model: str,
        path: str,
        max_seq_length=128,
        no_cuda=False,
    ):

        self.device = torch.device(
            "cuda:0" if torch.cuda.is_available() and not no_cuda else "cpu"
        )
        n_gpu = 1

        self.num_labels = 2
        self.label_list = ["entailement", "non_entailment"]

        self.tokenizer = BertTokenizer.from_pretrained(path, do_lower_case=True)

        # model_state_dict = torch.load(path, map_location='cpu')
        # self.model = BertForSequenceClassification.from_pretrained(bert_model, state_dict=model_state_dict, num_labels=self.num_labels)
        self.model = BertForSequenceClassification.from_pretrained(
            path, num_labels=self.num_labels
        )
        self.model.to(self.device)

        self.model.eval()

        self.max_seq_length = max_seq_length

    def predict(self, text_a_b, reverse=False):

        if reverse:
            input = [
                InputExample("test", text_b, text_a) for (text_a, text_b) in text_a_b
            ]
        else:
            input = [
                InputExample("test", text_a, text_b) for (text_a, text_b) in text_a_b
            ]

        eval_features = convert_examples_to_features(
            input, self.label_list, self.max_seq_length, self.tokenizer
        )
        input_ids = torch.tensor([f.input_ids for f in eval_features], dtype=torch.long)
        input_mask = torch.tensor(
            [f.input_mask for f in eval_features], dtype=torch.long
        )
        segment_ids = torch.tensor(
            [f.segment_ids for f in eval_features], dtype=torch.long
        )

        input_ids = input_ids.to(self.device)
        input_mask = input_mask.to(self.device)
        segment_ids = segment_ids.to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids, segment_ids, input_mask)
            probs = torch.softmax(logits, dim=1)

        probs = probs.detach().cpu()
        labels = [
            self.label_list[torch.max(probs[i], dim=0)[1].item()]
            for i in range(len(input))
        ]

        return labels, probs


class IntentPredictor:
    def __init__(self, model_path):

        print("Initializing BertNliPredictor... ", end="", flush=True)
        self.bert = BertNliPredictor(model_path, no_cuda=False)
        print("Done")

    # argmax
    def predict(
        self,
        input: str,
        tasks=None,
        task_key="task",
        example_key="examples",
        threshold=0.6,
    ):

        input = input.lower()

        # Intent
        nli_input = []
        for t in tasks:
            for e in t[example_key]:
                nli_input.append((input, e.lower()))

        results = self.bert.predict(nli_input)
        maxScore, maxIndex = results[1][:, 0].max(dim=0)

        maxScore = maxScore.item()
        maxIndex = maxIndex.item()

        if maxScore < threshold:
            intent = None
            intentS = ("None", 0, "None")
        else:
            index = -1
            for t in tasks:
                for e in t[example_key]:
                    index += 1

                    if index == maxIndex:
                        intent = t[task_key]
                        intentS = (intent, maxScore, e)

        return intentS


def intent_samples(task_info: dict):
    res = []
    for task in task_info:
        if "samples" in task_info[task]:
            res.append({"task": task, "examples": task_info[task]["samples"]})
    return res
