# ReadMe - Dialogue Info Layer Config

The Dialogue Info Layer handles NLU in Converse, and it is configurable through a yaml file. You can easily add new models or services and configure each model’s arguments for initialization and execution. The NLU models are served as gRPC services. You can also use their NLU models as REST APIs or Python function calls.
The path to Dialogue Info Layer is:

```
Converse/dialog_info_layer/dial_info.py
```

The configuration file of Dialogue Info Layer is:

```
Converse/bot_configs/dial_info_config.yaml
```

The contents of the yaml file are like this:

```
Models:
  ner:
    description: named entity extraction
    init_args:
      service_channel: localhost:50050
    call_args:
      returnSpan: True
  intent:
    description: nli based intent detection
    init_args:
      service_channel: localhost:50051
  negation:
    description: rule-based negation detection
    init_args:
      model_path: "./Converse/nlu/negation_detection/"
```

`ner`, `intent`, `negation`, `coref` are model names.
For each model, there are several **optional** fields for configuration:
`description`: this field indicates what is the model about
`init_args`: this field defines the arguments for model initialization
`call_args`: this filed defines the additional arguments for model call. When the model is called, there’s another argument i.e., `context`, which by default is `user utterance` in the current turn.
`context_args`: some model may need more context rather than just use the current `user utterance`. You can define the `win_size` here to use more `user utterances` and `bot responses` from previous turns. 

In order to make model call, for each model, we have a client script.
The NER client is defined as `class NER` in `Converse/nlu/ner_converse/client.py`
The intent client is defined as `class IntentDetection` in `Converse/nlu/intent_converse/client.py`
The negation client is defined as `class NegationDetection` in `Converse.nlu.negation_detection.negation_v2.py`

We provide an example ner model (based on TinyBERT6) and an example intent model (based on TinyBERT4).
You can use your own NLU models.
If you choose to use your own NER model, make sure that the final output of your model follows this format:

```
{"success": True, "probabilities": [
    {"label": "LOC", "probability": 0.98500675, "token": "san francisco", "span": {"start": 11, "end": 24}},
    {"label": "LOC", "probability": 0.9730393, "token": "redwood city", "span": {"start": 30, "end": 42}},
    {"label": "AP/LOCATION", "probability": 0.9101139, "token": "san francisco",
     "normalizedValue": "PlaceName:san francisco", "span": {"start": 11, "end": 24}}]}
```

`success` indicates whether this model call is successful.
The extracted tokens, corresponding labels and their probabilities are in `probabilities`. For each extracted token, `label`, `probability`, `token`, `span` are required keys, and `normalizedValue` is an optional key.
If you are not following this format, you need to modify `Converse/entity/entity.py` a lot to make it compatible with your model.
In `class NamedEntityExtractor` in `Converse/entity/entity.py`, we defined the mapping which maps NER model’s labels to the entity classes. If your model has different labels, you need to modify this class. You may also need to modify the entity classes we defined in `Converse/entity/entity.py`.

If you choose to use your own intent model, make sure that the final output of your model follows this format, here `sent` is an `optional` key, which is `the sample sentence with highest NLI score` when you use our NLI intent model.

```
{"success": True/ False, "intent": "your_intent_label", "prob": 0.0 ~ 1.0, "sent": "the sample sentence with highest NLI score"}
```

In most cases, you don’t need to change the negation model. If you want to use your own negation model, make sure that the output of your model follows this format,

```
{"wordlist": word tokenization results of the input sentence, "triplets": a list of (index_1, index_2, index_3)}
```

Here, `index_1` is the index of the negation word in word list, `index_2` and `index_3` are the start and end of the negation scope span. Note that the negation scope is `wordlist[index_2: index_3]`.

The intent model and negation model are used in `info_pipeline` and `intent_resolution` in `Converse/dialog_info_layer/dial_info.py`. If your own models don’t follow the output format, you need to modify the functions.
The `info_pipeline` function will call all the NLU models and do post-processing on model results.

If you want to add new NLU models other than NER, intent, negation, or replace the current models, here are the steps you need to follow:

* Wrap-up your model and create a `client.py`. You can serve your model in anyway, as long as there’s a function in `client.py` that can return model call results. You can refer to our `client.py` files if you need examples.
* Add your model name and necessary arguments in `Converse/bot_configs/dial_info_config.yaml`
* In `Converse/dialog_info_layer/dial_info.py`: 
    * import your model client and update `client_dict` (this dictionary stores the mapping from model name to model client)
    * Modify `info_pipeline` in `class InfoManager` if you need to do post-processing on your model results
* The `info_pipeline` functions is called in `Orchestrator` in `Converse/dialog_orchestrator/orchestrator.py`. You may need to modify this script and other scripts related to dialogue policy to make use of you new models.

