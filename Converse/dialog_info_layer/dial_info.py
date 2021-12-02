# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize

from Converse.dialog_context.dialog_context import DialogContext
from Converse.nlu.ner_converse.client import NER
from Converse.nlu.negation_detection.negation_v2 import NegationDetection
from Converse.nlu.intent_converse.client import IntentDetection
from Converse.config.task_config import TaskConfig, BotConfig, FAQConfig
from Converse.utils.yaml_parser import load_info_logic


SELECTED_POS_TAGS = {"PRP", "PRP$", "WP", "WP$"}
COREFERENCE_SKIP = {"i", "you", "we"}

client_dict = {"ner": NER, "intent": IntentDetection, "negation": NegationDetection}


# when adding new NLP model, should modify import, client_dict, collect_info(),
# and also maybe the logic in info_pipeline
class InfoManager:
    def __init__(
        self,
        info_config_file,
        task_config: TaskConfig = None,
        faq_config: FAQConfig = None,
    ):
        self.models_info = load_info_logic(info_config_file)
        self.models = {}
        self.negate_intent_threshold = 0.2
        for m_name in self.models_info:
            init_args = (
                self.models_info[m_name]["init_args"]
                if "init_args" in self.models_info[m_name]
                else {}
            )
            if task_config and m_name == "intent":
                init_args["task_config"] = task_config
                init_args["faq_config"] = faq_config
            self.models[m_name] = client_dict[m_name](**init_args)
            """
            An example of self.models:
            {'ner': NER client instance,
                'negation': NegationDetection client instance, ...}
            """

    def collect_info(self, utt: str, model_names: list, ctx: DialogContext):
        res = {}
        context = utt
        for name in model_names:
            assert name in client_dict
            if "context_args" in self.models_info[name]:
                context = ctx.user_history.extract_utt(
                    **self.models_info[name]["context_args"]
                )
            call_args = (
                self.models_info[name]["call_args"]
                if "call_args" in self.models_info[name]
                else {}
            )
            res[name] = self.models[name](context, **call_args)
            # sentence segmentation
            if name == "intent":
                sents_after_seg = sent_tokenize(utt)
                res["intent_seg"] = [
                    self.models[name](sent, **call_args) for sent in sents_after_seg
                ]
        return res

    def intent_resolution(self, intent_res_1, intent_res_2, negation_flag=False):
        got_intent_1 = intent_res_1["success"] if intent_res_1 else False
        got_intent_2 = intent_res_2["success"] if intent_res_2 else False

        intent_1 = intent_res_1["intent"] if got_intent_1 else ""
        intent_2 = intent_res_2["intent"] if got_intent_2 else ""
        prob1 = intent_res_1["prob"] if got_intent_1 else 0.0
        prob2 = intent_res_2["prob"] if got_intent_2 else 0.0

        res = {"intent": intent_1, "prob": prob1, "uncertain": False}

        if negation_flag:
            if (
                intent_1
                and intent_2
                and intent_1 == intent_2
                and prob2 - prob1 > self.negate_intent_threshold
            ):
                negate_intent = True
            else:
                negate_intent = False
        else:
            negate_intent = False

        if negate_intent:
            res["intent"] = "negative"
        if not negation_flag:
            if intent_2 and intent_2 != intent_1 and prob2 > prob1:
                res["intent"] = intent_2
                res["prob"] = prob2
        elif intent_2 and intent_2 == intent_1:
            if intent_1 != "positive" and intent_1 != "negative":
                res["uncertain"] = True

        return res

    def info_pipeline(
        self,
        asr_origin: str,
        asr_norm: str,
        ctx: DialogContext,
        models=["intent", "ner"],
    ):
        """
        This is the function that the orchestrator actually calls.
        It first collects all the NLU model results,
        then do intent resolution.
        """
        tokenized_utt = word_tokenize(asr_norm)
        pos_tags = nltk.pos_tag(tokenized_utt)
        ctx.store_utt(
            "spk1",
            "%Y-%m-%d %H:%M:%S",
            asr_norm,
            tokenized_text=tokenized_utt,
            pos_tags=pos_tags,
        )
        models = [m_name for m_name in self.models_info] if self.models_info else models
        res = self.collect_info(asr_norm, models, ctx)
        cur_mes = ctx.user_history.messages_buffer[-1]

        # sentence segmentation
        raw_sents = sent_tokenize(asr_norm)
        negation_flags = [False] * len(raw_sents)
        intent_2nd_res = [None] * len(raw_sents)
        negation_placeholder = "#@#"

        def remove_negation_word(negation_res, negation_placeholder="#@#"):
            """
            output:
                text_with_negation_words_removed: str
                tokenized_text_with_negation_placeholder: list of str(token)
                sents_with_negation_words_removed: list of str(sentence)
            """
            words = negation_res["wordlist"][::]
            triplets = negation_res["triplets"]
            for triplet in triplets:
                i = triplet[0]  # Index of the negation word
                words[i] = negation_placeholder
            text_with_negation_words_removed = " ".join(words)
            tokenized_text_with_negation_placeholder = words
            sents_with_negation_words_removed = sent_tokenize(
                text_with_negation_words_removed
            )
            negation_flags = [False] * len(sents_with_negation_words_removed)
            for i in range(len(negation_flags)):
                sents_with_negation_words_removed[
                    i
                ] = sents_with_negation_words_removed[i].replace(
                    negation_placeholder, ""
                )
                if sents_with_negation_words_removed[i] != raw_sents[i]:
                    negation_flags[i] = True
            text_with_negation_words_removed = " ".join(
                sents_with_negation_words_removed
            )
            return (
                text_with_negation_words_removed,
                tokenized_text_with_negation_placeholder,
                sents_with_negation_words_removed,
            )

        got_negation = (
            True
            if "negation" in res
            and "triplets" in res["negation"]
            and res["negation"]["triplets"]
            and res["negation"]["triplets"][0][0] != -1
            else False
        )
        if got_negation:
            (
                cur_mes.text_with_negation_words_removed,
                tokenized_text_with_negation_placeholder,
                sents_with_negation_words_removed,
            ) = remove_negation_word(res["negation"])
        else:
            (
                cur_mes.text_with_negation_words_removed,
                tokenized_text_with_negation_placeholder,
                sents_with_negation_words_removed,
            ) = (" ".join(tokenized_utt), tokenized_utt, sent_tokenize(asr_norm))

        # coreference resolution
        def find_entity(coref_res, cluster):
            """
            Find the actually entity value for each cluster.
            For example, if a cluster is ["the blue bike", "it"],
            the function will return "the blue bike".
            """
            words = coref_res["words"]
            entity = ""
            for span_s, span_e in cluster:
                pos_tags = nltk.pos_tag(words)
                # skip personal pronoun like I, you, we
                if " ".join(words[span_s:span_e]).lower() not in COREFERENCE_SKIP:
                    span_tags = set([t[1] for t in pos_tags[span_s:span_e]])
                    # skip pronoun, we only want actually entity here
                    if not span_tags.issubset(SELECTED_POS_TAGS):
                        entity = words[span_s:span_e]
                        break
            return entity

        def replace_corefed_entity(coref_res, tokenized_text_with_negation_placeholder):
            """
            output: str
            """
            predicted_clusters = coref_res["predicted_clusters"]
            utt_replaced_coref = []
            words = coref_res["words"][::]
            cur_utt_length = len(tokenized_text_with_negation_placeholder)
            start_ind = len(words) - len(tokenized_text_with_negation_placeholder)
            replaced_token_flags = [n for n in range(cur_utt_length)]
            replaced_span_dict = {}
            sig = "*"
            for cluster in predicted_clusters:
                entity_flag = False
                for span_s, span_e in cluster:
                    if (
                        span_s >= start_ind
                        and span_e <= start_ind + cur_utt_length
                        and " ".join(words[span_s:span_e]).lower()
                        not in COREFERENCE_SKIP
                    ):
                        span_tags = set(
                            [
                                t[1]
                                for t in pos_tags[
                                    span_s - start_ind : span_e - start_ind
                                ]
                            ]
                        )
                        if SELECTED_POS_TAGS & span_tags:
                            if not entity_flag:
                                entity = find_entity(coref_res, cluster)
                                entity_flag = True
                            if entity:
                                for ind in range(
                                    span_s - start_ind, span_e - start_ind
                                ):
                                    replaced_token_flags[ind] = sig
                                    replaced_span_dict[sig] = entity
                sig += "*"
            last_sign = ""  # for multi-token entity, only append once
            for ind, tok in enumerate(replaced_token_flags):
                if tok in replaced_span_dict:
                    if last_sign != tok:
                        utt_replaced_coref.extend(replaced_span_dict[tok])
                else:
                    utt_replaced_coref.append(
                        tokenized_text_with_negation_placeholder[ind]
                    )
                last_sign = tok
            utt_replaced_coref = " ".join(utt_replaced_coref)
            return utt_replaced_coref

        got_coref = (
            True
            if "coref" in res
            and "predicted_clusters" in res["coref"]
            and res["coref"]["predicted_clusters"]
            else False
        )
        cur_mes.utt_replaced_coref = (
            replace_corefed_entity(
                res["coref"], tokenized_text_with_negation_placeholder
            )
            if got_coref
            else " ".join(tokenized_text_with_negation_placeholder)
        )

        # intent resolution
        sents_to_adjust_for_coref = sent_tokenize(cur_mes.utt_replaced_coref)
        sents_tokenized_text_with_negation_placeholder = sent_tokenize(
            " ".join(tokenized_text_with_negation_placeholder)
        )
        coref_flags = [False] * len(sents_to_adjust_for_coref)
        for i in range(len(coref_flags)):
            sent_to_adjust_for_coref = sents_to_adjust_for_coref[i]
            if (
                sent_to_adjust_for_coref
                != sents_tokenized_text_with_negation_placeholder[i]
            ):
                coref_flags[i] = True
                intent_2nd_res[i] = self.models["intent"](
                    sent_to_adjust_for_coref.replace(negation_placeholder, "")
                )
            elif negation_flags[i]:
                intent_2nd_res[i] = self.models["intent"](
                    sents_with_negation_words_removed[i]
                )

        cur_mes.utt_replaced_coref = cur_mes.utt_replaced_coref.replace(
            negation_placeholder, ""
        )

        assert len(res["intent_seg"]) == len(intent_2nd_res) == len(negation_flags)
        intent_res = []
        for i in range(len(negation_flags)):
            intent_res.append(
                self.intent_resolution(
                    res["intent_seg"][i], intent_2nd_res[i], negation_flags[i]
                )
            )

        res["final_intent"] = None if not intent_res else intent_res[0]
        for i in range(1, len(intent_res)):
            if res["final_intent"]["uncertain"]:
                if not intent_res[i]["uncertain"]:
                    res["final_intent"] = intent_res[i]
                elif intent_res[i]["prob"] > res["final_intent"]["prob"]:
                    res["final_intent"] = intent_res[i]
            elif (
                res["final_intent"]["intent"] == "positive"
                or res["final_intent"]["intent"] == "negative"
            ):
                if intent_res[i]["intent"] != "positive":
                    res["final_intent"] = intent_res[i]
            elif (
                not intent_res[i]["uncertain"]
                and intent_res[i]["intent"] != "positive"
                and intent_res[i]["intent"] != "negative"
                and intent_res[i]["prob"] > res["final_intent"]["prob"]
            ):
                res["final_intent"] = intent_res[i]

        return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Dialog Information")
    parser.add_argument(
        "--info", type=str, default="./Converse/bot_configs/dial_info_config.yaml"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="./Converse/bot_configs/online_shopping/tasks.yaml",
    )
    args = parser.parse_args()

    task_config = TaskConfig(args.task)
    bot_config = BotConfig(args.task)
    info_manager = InfoManager(info_config_file=args.info, task_config=task_config)
    while True:
        utt = input("user input:")
        res = info_manager.info_pipeline(
            utt,
            utt,
            DialogContext(None, task_config=task_config, bot_config=bot_config),
        )
        user_id = "spk2"
        message_time = "%Y-%m-%d %H:%M:%S"
        print(res)
