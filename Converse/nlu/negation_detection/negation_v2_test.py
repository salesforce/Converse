# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

# Module name: Negation Detection v2 test

import argparse
from Converse.nlu.negation_detection.negation_v2 import NegationDetection

MODEL_DATA_PATH = "./Converse/nlu/negation_detection/"

### Test script
if __name__ == "__main__":
    import time

    # Instantiate
    negation_detection = NegationDetection(MODEL_DATA_PATH)

    # Test by a collection of sample sentences
    print("Test by a collection of sample sentences:")
    sents = [
        "we do not like the dog.",
        "I hate to eat egg",
        "today is very good",
        "i am unhappy today, so I would not go there.",
        "I don't like pickle, it is really disgusting",
        "I really hate updating my password",
        "I don't mind providing my social",
        "A whole combo pizza would not be a bad idea, thanks!",
    ]

    for sent in sents:
        start_time = time.time()
        results = negation_detection(sent)  # Call negation_detection function
        words = results["wordlist"]
        triplets = results["triplets"]
        time_spent = time.time() - start_time

        print("Input sentence = " + "'" + sent + "'")
        print("Words(word index|word):")
        numbered_words = ""
        for i, word in enumerate(words):
            numbered_words += "[" + str(i) + "]" + word + "|"
        print(numbered_words.strip("|"))
        for triplet in triplets:
            if triplet[0] == -1:
                print("No negation detected")
            else:
                print("Triplet: ", triplet)
                print("Negation word: ", words[triplet[0]])
                print("Scope: " + " ".join(words[triplet[1]: triplet[2]]))
        print("Time spent (in millisecond): " + str(1000 * time_spent))
        print("\n")
    print("\n")

    # Todo: Generate evaluation result on a set of test cases
