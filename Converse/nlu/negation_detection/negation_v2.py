# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

# Module name: Negation Detection v2
# Note: This negation detection is half model (NLTK) and half rule-based, may need further development


import nltk
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.sentiment.util import mark_negation
import codecs
import argparse
import string

nltk.download("punkt", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)

# Currently hard-coded dictionaries, need to consult with Wenpeng on these
NEGATION_ADVERBS = {
    "no",
    "without",
    "nil",
    "not",
    "n't",
    "never",
    "none",
    "neith",
    "nor",
    "non",
}
NEGATION_VERBS = {"deny", "reject", "refuse", "subside", "retract", "non"}
SELECTED_POS_TAGS = {
    "JJ",
    "JJR",
    "JJS",
    "RB",
    "RBR",
    "DT",
    "NN",
    "RBS",
    "TO",
    "VB",
    "VBD",
    "VBG",
    "VBN",
    "VBP",
    "VBZ",
}


class NegationDetection:
    def __init__(self, model_path: str):
        print("Initializing NegationDetection ... ", end="", flush=True)
        with codecs.open(model_path + "/negative_words.txt", "r", "utf-8") as f:
            self.neg_word_set = set([line.rstrip("\n") for line in f])
        print("Done")

    def scope_detection(
        self,
        word_pos_list,  # type: List[Tuple[str, str]]
        neg_id,  # type: int
    ):
        # type: (...) -> Tuple[int, int]
        """ Detect the corresponding scope for the negation id """
        """ ToDo: explain the meaning of the output """
        # print(word_pos_list,  neg_id)
        # ToDo: explain the below indictors are the indictors of what
        indictors = []  # type: List[int]
        for id, pair in enumerate(word_pos_list):
            # pair[0] is word, pair[1] is tag
            if (
                pair[1] in SELECTED_POS_TAGS
                and id != neg_id
                and (pair[0] not in string.punctuation)
            ):
                indictors.append(1)
            else:
                indictors.append(0)
        # print('indictors:', indictors)
        # exit(0)

        left_most = neg_id - 1
        while indictors[left_most] != 1:
            left_most -= 1
            if left_most < 0 and -left_most > len(indictors):  # bug fixing by Tian
                left_most += 1
                break
        right_most = neg_id + 1
        while right_most < len(indictors) and indictors[right_most] != 1:
            right_most += 1
        # print('left_most:',left_most)
        # print('right_most:',right_most)

        scope_list = []  # type: List[str]
        for i in range(right_most, len(word_pos_list)):
            if indictors[i] == 1:
                scope_list.append(word_pos_list[i][0])
            else:
                break
        # if neg_id - left_most > right_most - neg_id:
        #     for i in range(right_most, len(word_pos_list)):
        #         if word_pos_list[right_most][1] == 1:
        #             scope_list.append(word_pos_list[right_most][0])
        # else:
        #     for i in range(left_most, -1, -1):
        #         if word_pos_list[left_most][1] == 1:
        #             scope_list.append(word_pos_list[left_most][0])
        if (
            len(scope_list) > 0
        ):  # i == len(word_pos_list)-1 and indictors[i] == 1:   ### ToDo, clean here!
            return (right_most, right_most + len(scope_list))
        else:
            return (len(indictors), len(indictors))

    def __call__(
        self, strr: str  # type: str
    ):  # type: (str) -> Tuple[List[str], List[Tuple[int, int, int]]]
        """ Detect negation word and scope from an input sentence """
        """ Return the word list of the input sentence and the triplets (represented by three integers)
            of the detected negation parts.
            for a triplet, triplet[0] is the index of the negation word,
                        wordlist[triplet[1]:triplet[2]] is the corresponding negation scope """

        # Utilize the NLTK's built-in function mark_negation of the sentiment analysis
        strr = strr.lower()  # type: str
        wordlist = word_tokenize(strr)  # type: List[str]
        nltk_neg_mark_list = mark_negation(wordlist)
        nltk_start = -1
        nltk_end = -1

        for idd, word in enumerate(nltk_neg_mark_list):
            if word.find("_NEG") > 0:
                nltk_end = idd
                if nltk_start == -1:
                    nltk_start = idd
        if nltk_end != -1:
            nltk_end += 1
        if nltk_end > nltk_start:
            nltk_find = True
        else:
            nltk_find = False
        # print('nltk_find:', nltk_find)

        # Our tricks
        # Generate word-wise pos tags
        word_pos_list = pos_tag(wordlist)  # type: List[Tuple[str, str]]
        # print('wordlist:', wordlist)
        # print('word_pos_list:', word_pos_list)
        assert len(wordlist) == len(word_pos_list)

        fine_negation = False
        returned_triplets = []  # type: List[Tuple[int, int, int]]
        for id, pair in enumerate(word_pos_list):
            # pair[0] is word, pair[1] is tag
            word = pair[0]
            # pos = pair[1]
            if (
                word in NEGATION_ADVERBS
                or word in NEGATION_VERBS
                or word in self.neg_word_set
                or word[:2] == "un"
                or word[:3] == "dis"
            ):
                # ToDo: roughly explain this if condition
                # print('negate word:', word)
                scope_tuple = self.scope_detection(word_pos_list, id)
                # print('scope:', wordlist[scope_tuple[0]: scope_tuple[1]])
                returned_triplets.append((id, scope_tuple[0], scope_tuple[1]))
                fine_negation = True
        if fine_negation is False and nltk_find is False:
            # print('no negation detected')
            returned_triplets.append((-1, -1, -1))

        return {"wordlist": wordlist, "triplets": returned_triplets}
