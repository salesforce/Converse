# ReadMe - Dialogue Policy Configuration 

The dialogue policy follows human-designed rules (which can be customized) to decide the next dialogue action and generate the next response based on information from the Dialogue Information Manager and Dialogue State Manager.

The dialogue policy configuration works for all the bots. 

The dialogue policy configuration yaml file is

```
Converse/bot_configs/policy_config.yaml
```

**In most cases, you don’t actually need to modify this configuration file when you set up your bot.**
In case you want to modify this configuration file, we provide a simple guide for you.

There are 3 sections in this yaml file: `Flag`, `State`, and `Logic`.
`Flags` are information that is persistent within one conversational turn, such as `got_entity_info` which is a Boolean representing whether entities were extracted from the user’s inputs. `Flags` are defined in `class StatesWithinCurrentTurn` in `Converse/dialog_state_manager/dial_state_manager.py`.

`States` are information that is persistent between turns, such as the `cur_task` (current task) that Converse is trying to complete with the user. `States` are defined in `class DialogState` in  `Converse/dialog_state_manager/dial_state_manager.py`.

`Logic` is how the dialogue policy is routed by `Flags` and `States`. You can think of `Logic` as a tree structure. The routing process is like depth-first search. The dialogue policy will execute a dialogue action until it reaches a leaf node. The leaf nodes are the dialogue action names, which are corresponding to the functions in `class DialoguePolicy` in `Converse/dialog_policy/dial_policy.py`. The execution function of `Logic` is `policy_tree` in `class DialoguePolicy`. 
If no leaf node can be reached, the bot will execute `empty_response`. You can check the details of `empty_response `in `Converse/dialog_policy/dial_policy.py`.

```
Flag: 
  - got_info
  - polarity
  - got_intent
  - got_entity_info

State:
  - cur_task
  - confirm_continue
  - confirm_entity
  - confirm_intent
  - cur_entity_name
  - max_no_info_turn
  - continuous_no_info_turn
  - multiple_entities

Logic:
  - "not got_info":
      - "confirm_intent": 
          - task_confirm_handler
      - "confirm_entity": 
          - entity_confirm_handler
      - "not cur_task":
          - "confirm_continue":
              - "polarity == 1":
                  - greetings
              - "polarity == -1":
                  - goodbye
          - "continuous_no_info_turn > max_no_info_turn":
              - forward_to_human
          - empty_response 
      - "cur_entity_name": 
          - "polarity == -1":
              - "multiple_entities":
                  - no_entity_candidate_selected
              - fail_entity
          - "continuous_no_info_turn > max_no_info_turn":
              - fail_entity
          - empty_response
  - got_info:
      - "confirm_intent":
          - task_confirm_handler
      - "confirm_entity":
          - entity_confirm_handler
      - "got_intent and got_entity_info":
          - new_task_with_info
      - "got_intent":
          - got_new_task
      - "got_entity_info":
          - entity_info_handler
```

If you want to modify the current routing logic without adding new dialogue actions, you can simply modify `Logic`. 
For example, if `got_info` is `False` (indicates that the bot didn’t get intent or entity information in this turn), 
`cur_task` is `None` (indicates that there’s no task that needs to be finished right now), 
`confirm_continue` is `True` (indicates that bot is expecting the user to confirm whether or not continuing to chat, e.g., the bot responded  “`Is there anything else I can help you with?`” in the previous turn), 
and `polarity == 1` (indicates that user said something positive like “yes” in the current turn), the dialogue policy is routed to `greetings`. The bot will respond something like “`Hello! How may I help you?`”. 

If you change the logic of this part to

```
Logic:
  - "not got_info":
      ...
      - "not cur_task":
          - goodbye
  ...
```

Then if `got_info` is `False`, and `cur_task` is `None`, the bot will respond `goodbye` function's result, such as “`I am glad I can help. Have a nice day!`”.

You may need to make significant changes by adding a new dialogue action. Then you may need to also add new `Flags`, `States`, and update `Logic`. 
For example, if you want to add a new dialgogue action as the default action when `got_info` is `False` and no dialogue action is triggered, you can add `new_dial_act` to `Logic` and a new function in `class DialoguePolicy` in `Converse/dialog_policy/dial_policy.py`.

```
- "not got_info":
      ...
      - "cur_entity_name": 
          ...
      - new_dial_act
```

The modifications you may need to make to add a new dialogue action:

1. add a new dialogue action function (a function like `greetings`) in `class DialoguePolicy` in `Converse/dialog_policy/dial_policy.py`
2. add necessary `Flags` and `States` in `Converse/bot_configs/policy_config.yaml`
3. add the new `Flags` in `class StatesWithinCurrentTurn` in `Converse/dialog_state_manager/dial_state_manager.py`.
4. add the new `States` in `class DialogState` in `Converse/dialog_state_manager/dial_state_manager.py`

I hope this document can help when you need to modify `policy_config.yaml` if necessary.
