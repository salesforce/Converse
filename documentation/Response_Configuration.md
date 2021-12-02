# Response Configuration

`response_template.yaml` file is where you customize the responses for different scenarios. We defined several general conversation scenarios in the dialogue policy. For example, greeting, asking for an entity, starting a new task, etc. In each scenario, the dialogue policy will choose the corresponding response from the response template. By changing the response in the `response_template.yaml` file, you can change the responses in each predefined conversation scenario.

### How to change the existing response template by changing `response_template.yaml`:

Changing the existing response is simply change the string in the `response_template.yaml`. For example, the default response for asking for an entity in `response_template.yaml` is as follows:

```
ask_info:
    - Can I get your <Info>?
    - What is your <Info>?
```

When the bot asks for an entity, the dialogue policy will look into the `ask_info` response template, randomly choose one, and fill in the `<Info>` placeholder with the actual entity name. In a real conversation, for example, the check the weather task, the conversation will be like this:

> user: Could you please check the weather for me?

> bot: Sure, I’m happy to help you check the weather. **What is your zip code?**

If you change the response to another sentence as follows:

```
ask_info:
    - Could you please tell me your <Info>?
```

Then the conversation above about the check the weather will be like this:

> user: Could you please check the weather for me?

> bot: Sure, I’m happy to help you check the weather. **Could you please tell me your zip code?**

### How to add a new response template:

Although the response template file is general purpose and should cover most conversation scenarios, sometimes you would like to add your own conversation scenario and corresponding response template.

The `response_template.yaml` is used in Converse/response/response.py. If you want to add new templates, first, you need to specify **what** is the new response template in the `response_template.yaml` and add corresponding functions to choose or modify the response template in the response module in `response.py`. Second, the response module defined in `response.py` is used in `dial_policy.py` so you also need to modify `dial_policy.py` to specify **how** to use the new response functions. Third, the modifications to `dial_policy.py` may lead to the modifications to `Converse/dial_state_manager/dial_state_manager.py` and `bot_configs/policy_config.yaml` because the dialogue states and actions in these files let the dialog policy know **when** to use the response.

In summary, you may need to change the following files:

minimal changes (if you only want to add new response to existing conversation scenarios):

`bot_configs/response_template.yaml`: Add the desired response templates.
`response/response.py`: Add the response function to choose the response from the template and fill in the placeholder.

`dial_policy/dial_policy.py`: Change the function for the existing conversation scenario, specify how to use the new response function.

other possible changes (if you want to create new conversation scenatio):

`dial_state_manager/dial_state_manager.py`: Add new states to `DialogState` and new flags to `StateWithinCurrentTurn` that the new conversation scenario needs.

`bot_configs/policy_config.yaml`: Add the logic to decide the new conversation scenario based on the new states (`DialogState`) and flags (`StateWithinCurrentTurn`).

`dial_orchestrator/orchestrator.py` or `dial_policy/dial_policy.py`: Write the code to update the new states and flags during runtime.

`dial_policy/dial_policy.py`: Add a function for the new scenario. The function contains the detailed dialog action to take when the new scenario happens. The dialog action can be generating a response, changing certain dialogue states, calling other modules, etc.
