# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import codecs

import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text=None, cue_labels=None, scope_labels=None):
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
        self.text = text
        self.cue_labels = cue_labels
        self.scope_labels = scope_labels


def load_train_data(train_path):
    readfile = codecs.open(train_path, "r", "utf-8")
    sents = []
    poses = []
    cues = []
    scopes = []

    line_co = 0
    sent_size = 0
    examples = []
    instance_size = 0
    for line in readfile:
        if line_co == 0:
            line_group = []
        elif len(line.strip()) > 0:
            line_group.append(line.strip())
        else:
            sent_size += 1
            """preprocess this sentence"""
            assert len(line_group) > 0
            negation_size = (len(line_group[0].split("\t")) - 7) // 3
            if negation_size > 0:
                for i in range(negation_size):
                    """for each cue and scope, we create an training instance"""
                    sent = []
                    pos = []
                    cue = []
                    scope = []
                    for subline in line_group:
                        parts = subline.strip().split("\t")
                        # has_negation = True
                        sent.append(parts[3])
                        pos.append(parts[5])
                        cue.append("0" if parts[7 + i * 3] == "_" else "1")
                        scope.append("0" if parts[8 + i * 3] == "_" else "1")

                    guid = "train-" + str(instance_size)
                    examples.append(
                        InputExample(
                            guid=guid,
                            text=" ".join(sent),
                            cue_labels=cue,
                            scope_labels=scope,
                        )
                    )
                    instance_size += 1
            else:
                sent = []
                pos = []
                cue = []
                scope = []
                for subline in line_group:
                    parts = subline.strip().split("\t")
                    # has_negation = True
                    sent.append(parts[3])
                    pos.append(parts[5])
                    cue.append("0")
                    scope.append("0")
                # sents.append(sent)
                # poses.append(pos)
                # cues.append(cue)
                # scopes.append(scope)
                guid = "train-" + str(instance_size)
                examples.append(
                    InputExample(
                        guid=guid,
                        text=" ".join(sent),
                        cue_labels=cue,
                        scope_labels=scope,
                    )
                )
                instance_size += 1
            """create empty for next sentence"""
            line_group = []
        line_co += 1
    readfile.close()
    print("load over, training size:", len(examples), "sent size:", sent_size + 1)
    return examples


def load_test_data(train_path, filelist):

    # sents = []
    # poses = []
    # cues = []
    # scopes = []

    sent_size = 0
    examples = []
    instance_size = 0
    for fil in filelist:
        line_co = 0
        readfile = codecs.open(train_path + "/" + fil, "r", "utf-8")
        for line in readfile:
            if line_co == 0:
                line_group = []
            elif len(line.strip()) > 0:
                line_group.append(line.strip())
            else:
                sent_size += 1
                """preprocess this sentence"""
                assert len(line_group) > 0
                negation_size = (len(line_group[0].split("\t")) - 7) // 3
                if negation_size > 0:
                    for i in range(negation_size):
                        """for each cue and scope, we create an training instance"""
                        sent = []
                        pos = []
                        cue = []
                        scope = []
                        for subline in line_group:
                            parts = subline.strip().split("\t")
                            # has_negation = True
                            sent.append(parts[3])
                            pos.append(parts[5])
                            cue.append("0" if parts[7 + i * 3] == "_" else "1")
                            scope.append("0" if parts[8 + i * 3] == "_" else "1")

                        guid = "train-" + str(instance_size)
                        examples.append(
                            InputExample(
                                guid=guid,
                                text=" ".join(sent),
                                cue_labels=cue,
                                scope_labels=scope,
                            )
                        )
                        instance_size += 1
                else:
                    sent = []
                    pos = []
                    cue = []
                    scope = []
                    for subline in line_group:
                        parts = subline.strip().split("\t")
                        # has_negation = True
                        sent.append(parts[3])
                        pos.append(parts[5])
                        cue.append("0")
                        scope.append("0")
                    guid = "train-" + str(instance_size)
                    examples.append(
                        InputExample(
                            guid=guid,
                            text=" ".join(sent),
                            cue_labels=cue,
                            scope_labels=scope,
                        )
                    )
                    instance_size += 1
                """create empty for next sentence"""
                line_group = []
            line_co += 1
        readfile.close()
    print("load over, test size:", len(examples), "sent size:", sent_size + 1)
    return examples


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(
        self,
        input_ids,
        input_mask,
        segment_ids,
        cue_label_ids,
        scope_label_ids,
        valid_ids=None,
        label_mask=None,
    ):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.cue_label_ids = cue_label_ids
        self.scope_label_ids = scope_label_ids
        self.valid_ids = valid_ids
        self.label_mask = label_mask


def convert_examples_to_features(examples, label_list, max_seq_length, tokenizer):
    """Loads a data file into a list of `InputBatch`s."""
    """
    guid, text=None, cue_labels=None, scope_labels
    """
    """
    ["O", "B-MISC", "I-MISC",  "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "[CLS]", "[SEP]"]
    ['0','1']
    """
    """label index 0 is kept for padding fake labels"""
    # label_map = {label : i for i, label in enumerate(label_list,1)}
    label_map = {label: i for i, label in enumerate(label_list)}

    features = []
    for (ex_index, example) in enumerate(examples):
        textlist = example.text.split()
        cue_labellist = example.cue_labels
        scope_labellist = example.scope_labels

        tokens = []  # subtoken-level
        cue_labels = []  # word-level
        scope_labels = []  # word-level
        valid = []  # subtoken level
        label_mask = []  # word level, shared by cue and scope
        for i, word in enumerate(textlist):
            token = tokenizer.tokenize(word)  # may be a list
            tokens.extend(token)
            label_cue_i = cue_labellist[i]
            label_scope_i = scope_labellist[i]
            """seems we only consider the first token after the tokenzier"""
            for m in range(len(token)):
                if m == 0:
                    """word level"""
                    cue_labels.append(label_cue_i)
                    scope_labels.append(label_scope_i)
                    label_mask.append(1)
                    """subtoken level"""
                    valid.append(1)
                else:
                    """subtoken level"""
                    valid.append(0)
        if len(tokens) >= max_seq_length - 1:
            tokens = tokens[0 : (max_seq_length - 2)]
            valid = valid[0 : (max_seq_length - 2)]
            cue_labels = cue_labels[0 : (max_seq_length - 2)]
            scope_labels = scope_labels[0 : (max_seq_length - 2)]
            label_mask = label_mask[0 : (max_seq_length - 2)]

        ntokens = []
        segment_ids = []
        cue_label_ids = []
        scope_label_ids = []
        """add special token in the beginning"""
        ntokens.append("[CLS]")
        segment_ids.append(0)
        # cue_label_ids.append(label_map["[CLS]"])
        # scope_label_ids.append(label_map["[CLS]"])
        """#we do not think the pad token is valid to train"""
        cue_label_ids.append(0)
        scope_label_ids.append(0)
        valid.insert(0, 0)
        label_mask.insert(0, 0)

        for i, token in enumerate(tokens):
            ntokens.append(token)
            segment_ids.append(0)
            if i < len(cue_labels):
                cue_label_ids.append(label_map[cue_labels[i]])
                scope_label_ids.append(label_map[scope_labels[i]])

        """add special token in the end"""
        ntokens.append("[SEP]")
        segment_ids.append(0)
        valid.append(0)
        label_mask.append(0)
        cue_label_ids.append(0)
        scope_label_ids.append(0)

        input_ids = tokenizer.convert_tokens_to_ids(ntokens)
        input_mask = [1] * len(input_ids)
        assert len(cue_label_ids) == len(label_mask)
        assert len(scope_label_ids) == len(label_mask)
        # label_mask = [1] * len(label_ids)
        while len(input_ids) < max_seq_length:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)
            cue_label_ids.append(0)  # pad 0, it shows why regular labels start from 1
            scope_label_ids.append(0)  # pad 0, it shows why regular labels start from 1
            """???why valid is 1 rather than 0"""
            valid.append(0)
            label_mask.append(0)
        while len(cue_label_ids) < max_seq_length:
            cue_label_ids.append(0)
            scope_label_ids.append(0)
            label_mask.append(0)

        """subtoken level"""
        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length
        assert len(valid) == max_seq_length
        """??? why we need make them length == max; word level"""
        assert len(cue_label_ids) == max_seq_length
        assert len(scope_label_ids) == max_seq_length
        assert len(label_mask) == max_seq_length

        if ex_index < 5:
            logger.info("*** Example ***")
            logger.info("guid: %s" % (example.guid))
            logger.info("tokens: %s" % " ".join([str(x) for x in tokens]))
            logger.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            logger.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
            logger.info("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
            # logger.info("cue_labels: %s (id = %d)" % (example.cue_labels, cue_label_ids))
            # logger.info("scope_labels: %s (id = %d)" % (example.scope_labels, scope_label_ids))

        features.append(
            InputFeatures(
                input_ids=input_ids,
                input_mask=input_mask,
                segment_ids=segment_ids,
                cue_label_ids=cue_label_ids,
                scope_label_ids=scope_label_ids,
                valid_ids=valid,
                label_mask=label_mask,
            )
        )
    return features
