# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


import random
import numpy as np
import logging
import json
from collections import defaultdict

import torch
import torch.nn.functional as F
from torch.utils.data import TensorDataset, RandomSampler, DataLoader, SequentialSampler

from transformers import AdamW, get_linear_schedule_with_warmup

from sklearn.metrics import (
    classification_report,
    f1_score,
    accuracy_score,
    precision_score,
    recall_score,
)

THRESHOLDS = [i * 0.1 for i in range(11)]


class DisableLogger:
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, a, b, c):
        logging.disable(logging.NOTSET)


def get_logger(name):
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO,
    )
    logger = logging.getLogger(name)
    return logger


def truncate_seq_pair(tokens_a, tokens_b, max_length):

    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_length:
            break
        if len(tokens_a) > len(tokens_b):
            tokens_a.pop()
        else:
            tokens_b.pop()


def truncate_single_seq(tokens, max_length):
    while True:
        total_length = len(tokens)
        if total_length <= max_length:
            break
        tokens.pop()


def get_optimizer(model, t_total, args):

    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [
                p
                for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.01,
        },
        {
            "params": [
                p
                for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]

    optimizer = AdamW(
        optimizer_grouped_parameters, lr=args.learning_rate, eps=args.adam_epsilon
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(t_total * args.warmup_proportion),
        num_training_steps=t_total,
    )

    return optimizer, scheduler


def get_train_dataloader(train_features, train_batch_size):
    all_input_ids = torch.tensor(
        [f.input_ids for f in train_features], dtype=torch.long
    )
    all_input_mask = torch.tensor(
        [f.input_mask for f in train_features], dtype=torch.long
    )
    all_segment_ids = torch.tensor(
        [f.segment_ids for f in train_features], dtype=torch.long
    )
    all_label_ids = torch.tensor([f.label_id for f in train_features], dtype=torch.long)
    train_data = TensorDataset(
        all_input_ids, all_input_mask, all_segment_ids, all_label_ids
    )
    train_sampler = RandomSampler(train_data)
    train_dataloader = DataLoader(
        train_data, sampler=train_sampler, batch_size=train_batch_size
    )

    return train_dataloader


def get_eval_dataloader(eval_features, eval_batch_size):
    all_input_ids = torch.tensor([f.input_ids for f in eval_features], dtype=torch.long)
    all_input_mask = torch.tensor(
        [f.input_mask for f in eval_features], dtype=torch.long
    )
    all_segment_ids = torch.tensor(
        [f.segment_ids for f in eval_features], dtype=torch.long
    )
    all_label_ids = torch.tensor([f.label_id for f in eval_features], dtype=torch.long)
    eval_data = TensorDataset(
        all_input_ids, all_input_mask, all_segment_ids, all_label_ids
    )
    eval_sampler = SequentialSampler(eval_data)
    eval_dataloader = DataLoader(
        eval_data, sampler=eval_sampler, batch_size=eval_batch_size
    )

    return eval_dataloader


def process_train_batch(batch, device):
    input_mask = batch[1]
    batch_max_len = input_mask.sum(dim=1).max().item()

    batch = tuple(t.to(device) for t in batch)
    input_ids, input_mask, segment_ids, label_ids = batch
    input_ids = input_ids[:, :batch_max_len]
    input_mask = input_mask[:, :batch_max_len]
    segment_ids = segment_ids[:, :batch_max_len]

    return input_ids, input_mask, segment_ids, label_ids


def loss_with_label_smoothing(label_ids, logits, label_distribution, coeff, device):
    # label smoothing
    label_ids = label_ids.cpu()
    target_distribution = torch.FloatTensor(logits.size()).zero_()
    for i in range(label_ids.size(0)):
        target_distribution[i, label_ids[i]] = 1.0
    target_distribution = (
        coeff * label_distribution.unsqueeze(0) + (1.0 - coeff) * target_distribution
    )
    target_distribution = target_distribution.to(device)

    # KL-div loss
    prediction = torch.log(torch.softmax(logits, dim=1))

    loss = F.kl_div(prediction, target_distribution, reduction="mean")

    return loss


class IntentExample:
    def __init__(self, text, label):
        self.text = text
        self.label = label
        self.paras = []


def load_intent_examples(file_path):
    examples = []

    with open("{}/seq.in".format(file_path), "r", encoding="utf-8") as f_text, open(
        "{}/label".format(file_path), "r", encoding="utf-8"
    ) as f_label:
        for text, label in zip(f_text, f_label):
            if ";" in label:
                continue

            e = IntentExample(text.strip(), label.strip())
            examples.append(e)

    return examples


def load_intent_datasets(train_file_path, dev_file_path):
    train_examples = load_intent_examples(train_file_path)
    dev_examples = load_intent_examples(dev_file_path)

    return train_examples, dev_examples


def sample(N, examples):
    labels = {}  # unique classes

    for e in examples:
        if e.label in labels:
            labels[e.label].append(e.text)
        else:
            labels[e.label] = [e.text]

    sampled_examples = []
    for l in labels:
        random.shuffle(labels[l])
        if l == "oos":
            examples = labels[l][:N]
        else:
            examples = labels[l][:N]
        sampled_examples.append({"task": l, "examples": examples})

    return sampled_examples


class InputExample(object):
    def __init__(self, text_a, text_b, label=None, uid=None):
        self.text_a = text_a
        self.text_b = text_b
        self.label = label
        self.id = uid


class InputFeatures(object):
    def __init__(self, input_ids, input_mask, segment_ids, label_id):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_id = label_id


def load_nli_examples(file_path):
    examples = []
    with open(file_path, "r") as f:
        for line in f:
            fields = line.strip().split("\t")
            e = InputExample(fields[0], fields[1], fields[2])
            examples.append(e)

    return examples


# Evaluation metrics
def accuracy(out, labels):
    outputs = np.argmax(out, axis=1)
    return np.sum(outputs == labels)


def calc_in_f1(examples, in_domain_preds, thresholds):
    in_f1 = []
    preds_over_threshold = [[] for _ in thresholds]
    truth = [e.label for e in examples]
    for e, (conf, pred) in zip(examples, in_domain_preds):
        for i in range(len(preds_over_threshold)):
            if conf >= thresholds[i]:
                preds_over_threshold[i].append(pred)
            else:
                preds_over_threshold[i].append("oos")
    for i in range(len(preds_over_threshold)):
        f1 = f1_score(truth, preds_over_threshold[i], average="macro")
        in_f1.append(f1)
    return in_f1


def calc_in_acc(examples, in_domain_preds, thresholds):
    in_acc = [0.0] * len(thresholds)

    for e, (conf, pred) in zip(examples, in_domain_preds):
        for i in range(len(in_acc)):
            if pred == e.label and conf >= thresholds[i]:
                in_acc[i] += 1

    for i in range(len(in_acc)):
        in_acc[i] = in_acc[i] / len(examples)

    return in_acc


def calc_oos_recall(oos_preds, thresholds):
    oos_recall = [0.0] * len(thresholds)

    for (conf, pred) in oos_preds:
        for i in range(len(oos_recall)):
            if conf < thresholds[i]:
                oos_recall[i] += 1

    if len(oos_preds) > 0:
        for i in range(len(oos_recall)):
            oos_recall[i] = oos_recall[i] / len(oos_preds)

    return oos_recall


def calc_oos_precision(in_domain_preds, oos_preds, thresholds):

    if len(oos_preds) == 0:
        return [0.0] * len(thresholds)

    oos_prec = []

    for th in thresholds:
        oos_output_count = 0
        oos_correct = 0

        for pred in in_domain_preds:
            if pred[0] < th:
                oos_output_count += 1

        for pred in oos_preds:
            if pred[0] < th:
                oos_output_count += 1
                oos_correct += 1

        if oos_output_count == 0:
            oos_prec.append(0.0)
        else:
            oos_prec.append(oos_correct / oos_output_count)

    return oos_prec


def calc_oos_f1(oos_recall, oos_prec):
    oos_f1 = []

    for r, p in zip(oos_recall, oos_prec):
        if r + p == 0.0:
            oos_f1.append(0.0)
        else:
            oos_f1.append(2 * r * p / (r + p))

    return oos_f1


def calc_oos_acc(in_domain_preds, oos_preds, thresholds):
    if len(oos_preds) == 0:
        return [0.0] * len(thresholds)

    oos_acc = []

    for th in thresholds:
        oos_correct = 0

        for pred in in_domain_preds:
            if pred[0] > th:
                oos_correct += 1

        for pred in oos_preds:
            if pred[0] < th:
                oos_correct += 1
        acc = oos_correct / (len(in_domain_preds) + len(oos_preds)) * 1.0
        oos_acc.append(acc)
    return oos_acc


def print_results(thresholds, in_f1, in_acc, oos_recall, oos_prec, oos_f1, oos_acc):
    results = [
        [
            "Threshold",
            "In-F1",
            "In-domain accuracy",
            "OOS recall",
            "OOS precision",
            "OOS F1",
            "OOS Acc",
        ]
    ]

    for i in range(len(thresholds)):
        entry = [
            thresholds[i],
            100.0 * in_f1[i],
            100.0 * in_acc[i],
            100.0 * oos_recall[i],
            100.0 * oos_prec[i],
            100.0 * oos_f1[i],
            100.0 * oos_acc[i],
        ]
        results.append(entry)

    # print(tabulate(results[1:], results[0], tablefmt="grid"))


def save_to_file(folder_name, file_predictions, f, do_final_test=None):
    stats_lists = defaultdict(list)

    acc = []
    oos_acc = []
    oos_prec = []
    # with open(file_name_stats, 'r') as f:
    for line in f:
        acc.append([])
        oos_acc.append([])
        oos_prec.append([])

        for elms in line.strip().split():
            elms = elms.split(",")

            acc[-1].append(float(elms[0]))
            oos_acc[-1].append(float(elms[1]))
            oos_prec[-1].append(float(elms[2]))
    acc = torch.FloatTensor(acc) * 100
    oos_acc = torch.FloatTensor(oos_acc) * 100
    oos_prec = torch.FloatTensor(oos_prec) * 100
    # all_files.append(file_name.split('/')[-1])

    # all_acc.append(acc)
    # all_oos_acc.append(oos_acc)

    all_means_In_domain = acc.mean(dim=0)
    all_stds_In_domain = acc.std(dim=0)
    all_mins_In_domain = acc.min(dim=0)[0]
    all_maxs_In_domain = acc.max(dim=0)[0]

    all_means_OOS = oos_acc.mean(dim=0)
    all_stds_OOS = oos_acc.std(dim=0)
    all_mins_OOS = oos_acc.min(dim=0)[0]
    all_maxs_OOS = oos_acc.max(dim=0)[0]

    all_means_OOS_prec = oos_prec.mean(dim=0)
    all_stds_OOS_prec = oos_prec.std(dim=0)
    all_mins_OOS_prec = oos_prec.min(dim=0)[0]
    all_maxs_OOS_prec = oos_prec.max(dim=0)[0]

    combinated_means = (all_means_In_domain + all_means_OOS) / 2.0
    best_threshold_index = torch.argmax(combinated_means)

    best_mean_in_domain_acc = all_means_In_domain[best_threshold_index].item()
    best_mean_oos_acc = all_means_OOS[best_threshold_index].item()
    best_mean_oos_prec = all_means_OOS_prec[best_threshold_index].item()

    best_std_in_domain = all_stds_In_domain[best_threshold_index].item()
    best_std_oos = all_stds_OOS[best_threshold_index].item()
    best_std_oos_prec = all_stds_OOS_prec[best_threshold_index].item()

    best_min_in_domain = all_mins_In_domain[best_threshold_index].item()
    best_min_oos = all_mins_OOS[best_threshold_index].item()
    best_min_oos_prec = all_mins_OOS_prec[best_threshold_index].item()

    best_max_in_domain = all_maxs_In_domain[best_threshold_index].item()
    best_max_oos = all_maxs_OOS[best_threshold_index].item()
    best_max_oos_prec = all_maxs_OOS_prec[best_threshold_index].item()

    folder_model_name = folder_name.split("/")[-2]
    stats_lists[folder_model_name] = {}
    stats_lists[folder_model_name]["Best Setting"] = folder_model_name
    stats_lists[folder_model_name]["Best Threshold"] = (
        float(best_threshold_index) / 10.0
    )

    stats_lists[folder_model_name]["Best Mean In-domain Acc"] = best_mean_in_domain_acc
    stats_lists[folder_model_name]["Best Mean Out-of-Scope Acc"] = best_mean_oos_acc
    stats_lists[folder_model_name]["Best Mean Out-of-Scope Prec"] = best_mean_oos_prec

    stats_lists[folder_model_name]["Best Stds In-domain Value"] = best_std_in_domain
    stats_lists[folder_model_name]["Best Stds Out-of-Scope Value Acc"] = best_std_oos
    stats_lists[folder_model_name][
        "Best Stds Out-of-Scope Value Prec"
    ] = best_std_oos_prec

    stats_lists[folder_model_name]["Best Mins In-domain Value"] = best_min_in_domain
    stats_lists[folder_model_name]["Best Mins Out-of-Scope Value Acc"] = best_min_oos
    stats_lists[folder_model_name][
        "Best Mins Out-of-Scope Value Prec"
    ] = best_min_oos_prec

    stats_lists[folder_model_name]["Best Maxs In-domain Value"] = best_max_in_domain
    stats_lists[folder_model_name]["Best Maxs Out-of-Scope Value Acc"] = best_max_oos
    stats_lists[folder_model_name][
        "Best Maxs Out-of-Scope Value Prec"
    ] = best_max_oos_prec

    stats_lists[folder_model_name][
        "Best Mean In-domain list"
    ] = all_means_In_domain.tolist()
    stats_lists[folder_model_name][
        "Best Mean Out-of-Scope list"
    ] = all_means_OOS.tolist()
    stats_lists[folder_model_name][
        "Best Mean Out-of-Scope list Prec"
    ] = all_means_OOS_prec.tolist()

    stats_lists[folder_model_name][
        "Best Stds In-domain list"
    ] = all_stds_In_domain.tolist()
    stats_lists[folder_model_name][
        "Best Stds Out-of-Scope list"
    ] = all_stds_OOS.tolist()
    stats_lists[folder_model_name][
        "Best Stds Out-of-Scope list Prec"
    ] = all_stds_OOS_prec.tolist()

    stats_lists[folder_model_name][
        "Best Mins In-domain list"
    ] = all_mins_In_domain.tolist()
    stats_lists[folder_model_name][
        "Best Mins Out-of-Scope list"
    ] = all_mins_OOS.tolist()
    stats_lists[folder_model_name][
        "Best Mins Out-of-Scope list Prec"
    ] = all_mins_OOS_prec.tolist()

    stats_lists[folder_model_name][
        "Best Maxs In-domain list"
    ] = all_maxs_In_domain.tolist()
    stats_lists[folder_model_name][
        "Best Maxs Out-of-Scope list"
    ] = all_maxs_OOS.tolist()
    stats_lists[folder_model_name][
        "Best Maxs Out-of-Scope list Prec"
    ] = all_maxs_OOS_prec.tolist()

    stats_lists[folder_model_name]["All_Trials"] = []

    for i in range(len(acc)):
        task_trail = {}
        task_trail["Trial"] = i

        task_trail["In-domain ACC"] = acc[i][best_threshold_index].item()
        task_trail["Out-of-Scope ACC"] = oos_acc[i][best_threshold_index].item()
        # task_trail["Unique Word Ratio"] = unique_words_ratios[i]
        task_trail["Eval_Preds"] = file_predictions[i]
        stats_lists[folder_model_name]["All_Trials"].append(task_trail)
    # print(stats_lists)
    if do_final_test:
        # out_file_name = folder_name + "result_and_predictions_VALID.json"
        out_file_name = folder_name + "result_and_predictions_TEST.json"
    else:
        # out_file_name = folder_name + "result_and_predictions.json"
        out_file_name = folder_name + "result_and_predictions_MASK_hard_oos-Top_2.json"

    with open(out_file_name, "w") as outfile:
        json.dump(stats_lists, outfile, indent=4)


def read_label_list(fp):
    label_list = []
    with open(fp, "r") as handler:
        for line in handler:
            new_line = line.strip()
            if new_line:
                label_list.append(new_line)
    return label_list
