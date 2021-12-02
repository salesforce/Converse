There are three sections in the task configuration: bot configuration, task configuration, and FAQ/small-talk Configuration. **Bot configuration** contains the bot name and the bot type (text bot or voice bot). We define the tasks the bot supports under **task configuration**. A task usually requires multiple turns of dialogue. And we define the FAQ/small-talks under **FAQ/small-talk configuration**. FAQ/small-talk means a one-turn dialogue that can happen anywhere in a conversation in the Converse system.

The documentation is in the following format:

`configuration key`: configuration value type + configuration value description → default value.

```
A possible usage example
```

> Bot: A possible conversation example regarding this configuration key

> User: A possible conversation example regarding this configuration key

If the configuration key is **required**, there will be no default value. The configuration key with a default value is **optional**. That is to say, if the optional configuration is not specified in the YAML file, the bot will use the default value.

### Bot Configuration:

- `text_bot`: A boolean value that indicates whether the bot is a text bot. If a voice module will be incorporated into the bot, the value should be set to False. → default is True.
- `bot_name`: A string value that is the name of the bot. This will be used in the `greeting` response in the response_template.yaml → default is “your Converse bot”.

```
Bot:
    text_bot: true
    bot_name: Vaccine Checker Bot of Salesforce Health
```

### Task Configuration:

- `description`: A _required_ field takes a string value that describes the task. This will be used in the `suggest_tasks` and `got_intent` response in the response_template.yaml. If the user's response does not match the intents that the bot supports, then the suggest_tasks response will list the task descriptions of supported tasks.

  ```
  Authentication:
      description: authenticate the user's name and security question
  ```

- `samples`: A list of strings that are used for the intent model to detect the task from the user’s utterance. The samples don’t have to be the exact sentence the user will use. Usually, 3-5 samples will work. Note that punctuation like question marks is not required in these samples. It can be empty when you don’t want a task to be triggered by any user utterances (if you don't want use Converse's intent detection model to detect this task). → default is an empty list.

  ```
  check_application_status:
      samples:
          - check application status
          - check my application
          - what's my application status
          - how is my application going
          - is there any update on my application status
  ```

- `repeat`: A boolean value whether to repeat this task after the task succeeds (i.e., prompt the user to repeat this task) → default is False.

  ```
  check_the_weather:
      repeat:false
  ```

  &ensp;&ensp;Here is an example of the bot behavior:

  &ensp;&ensp;if repeat is True:

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: The weather in Palo Alto is sunny. Your request is completed. **Do you want to check the weather again?**

  > user: Yes, please. How about the weather in San Francisco?

  &ensp;&ensp;if repeat is False:

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: The weather in Palo Alto is sunny. Your request is completed. **Is there anything else I can help you with?**

  > user: Yes. I want to check the weather for another place.

- `repeat_response`: A list of strings that will be randomly selected and be used to prompt the user when repeating this task. → default is the `task_repeat_response` in the response_template.yaml.

  ```
  check_the_weather:
      repeat_response:
          - Do you want to check the weather for another place?
          - Wanna know the weather in another area?
  ```

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: The weather in Palo Alto is sunny. Your request is completed. **Do you want to check the weather for another place?**

  > user: Yes, please. How about the weather in San Francisco?

- `max_turns`: A numeric value indicating the maximum allowed turns for this task to complete → default is infinity.

- `finish_response`: A string that is a prompt to indicate the current task is finished. It takes a dictionary of a list of strings with keys `success` and `failure`. One of the corresponding responses will be randomly selected and output to the user. → default is the `task_finish_response` in the response_template.yaml.

  ```
  check_the_weather:
      finish_response:
          success:
              - ""
          failure:
              - "Sorry, I don't know the weather in this area."
  ```

  success:

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: The weather in Palo Alto is sunny. Is there anything else I can help you with?

  failure:

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: API call failed. **Sorry, I don't know the weather in this area.** Is there anything else I can help you with?

- `task_finish_function`: A string that is the name of a customizable function or a URL of a RESTful API that will be called after the task is completed. You can define whatever function you need in entity_functions.py and put the function name here. Check an example task finish function [here](https://github.com/MetaMind/eloq_dial/blob/main/Converse/entity_backend/entity_functions.py#L125). If it is a URL of a RESTful API, there's no additional code to add, you just need to make sure the API works. The default input of the task finish function is all the entities collected in the task. The output of the task finish function is a [resp](https://github.com/MetaMind/eloq_dial/blob/e7e2193de7bb15adfdf8224fb19a77bca2e0cc03/Converse/utils/utils.py#L74) object. Typical usage of the task finish function is to use the collected entities as arguments to make an external API call. The API call can pass the information to other services. -> defualt is an empty string.

  Assume the `where_do_people_care_about_the_weather_most` function is a counter for the `check_the_weather` task, it counts the user specified zip code and tells the bot builder where do people care about the weather most. Adding the following configuration to `check_the_weather` won't change the conversation behavior of the bot, but we have the data of where do people care about the weather most, which can be used in other services.

  ```
  check_the_weather:
      task_finish_function: where_do_people_care_about_the_weather_most
  ```

  > user: Could you please check the weather for zip code 94301 for me?

  > bot: The weather in Palo Alto is sunny. Is there anything else I can help you with?

- `entities`: A dictionary of TaskEntity objects. Each key in the dictionary is the name of an entity that will be used in the task. By default, all of the entities should be present in the entity configuration file `entity_config.yaml`. Below describes the structure of the TaskEntity dictionary with the following keys & values:

  Here's a configuration example and the corresponding bot behavior with the most basic setting of `entities`. Note that most of the fields are set to the default value.

  ```
  check_the_weather:
      entities:
        zip_code:
          prompt:
          function: check_weather
          confirm: False
          retrieve: True
          confirm_retrieved: True
          response:
          forget: True
      entity_groups:
        zip_code_group:
          - zip_code
      success:
        AND:
          - API:
              - zip_code_group

  ```

  > user: Could you please check the weather for me?

  > bot: Sure, what is your zip code?

  > user: The zip code is 94301.

  > bot: The weather in Palo Alto is sunny. Is there anything else I can help you with?

  - `prompt`: takes a list of strings as prompts given to the user when the bot asks for this entity. -> default is `ask_info` template in `response_template.yaml`

    ```
    check_the_weather:
        entities:
          zip_code:
            prompt:
              - could you please tell me the zip code of the area you want to check?
    ```

    > user: Could you please check the weather for me?

    > bot: Sure, **could you please tell me the zip code of the area you want to check?**

  - `function`: A _required_ key taking a string value, which is a call to a function when this particular entity is retrieved from the user during this task. For how to add these functions and running them, see, for example, [here](https://github.com/MetaMind/eloq_dial/blob/e975194fefc97d3859bf536839006253e391107a/service_backend.py#L51). Write the function in `Converse/entity_backend/service_backend.py` and run the service backend as described in README.

    Note that the `check_weather` function in the example takes the user's zip code as input and returns the weather.

  - `retrieve`: takes a boolean value specifying whether to retrieve this entity from the user’s input in the previous turns. For example, if this entity has been already provided by the user for a different task, then this entity is already stored in the system and can be pulled for this task. → default is True

    ```
    check_the_weather:
        entities:
          retrieve: True
    ```

    > user: Could you please check the order status for me? My zip code is 94301 and my order id is CA12345678.

    > bot: Sure, your order status is delivered. Is there anything else I can help you with?

    > user: What is the weather today?

    > bot: I’m happy to help you check the weather, **the weather in Palo Alto is sunny**, is there anything else I can help you with?

  - `confirm`: A boolean value to indicate whether the system should verify the retrieved entity with the user before accepting it → default is False

    ```
    check_the_weather:
        entities:
          confirm: True
    ```

    > user: The zip code is 94301.

    > bot: Got it. **The zip code is 94301, right?**

  - `confirm_retrieved`: same as `confirm`, but applies to only retrieved entities, i.e., any entities that the user provided in previous turns (sometime in the previous turns excluding the very last user input) → default is True

    ```
    check_the_weather:
        entities:
          confirm_retrieved: True
    ```

    > user: Could you please check the order status for me? My zip code is 94301 and my order id is CA12345678.

    > bot: Sure, your order status is delivered. Is there anything else I can help you with?

    > user: What is the weather today?

    > bot: I’m happy to help you check the weather. **Your zip code is 94301, right?**

  - `response`: takes a list of strings to be used to prompt the user after successfully accepting this entity during this task.

    If you leave this field empty, the bot will use a default entity response in `response_template.yaml` based on the action type of the entity (see explanation for _action type_ in the following `success` field section). For example, if the action type of the `zip_code` entity is `API`, the default entity response is a placeholder `<info>`, which will be replaced by the response returned by the specified entity `function` in entity backend.

    This field is designed to overwrite the default entity response conveniently. If the desired response doesn't depend on the entity, you can just list the responses. If the desired response depend on the entity, you can put a placeholder `<info>`, the placeholder will be replaced by the response returned by the specified entity `function` in entity backend. -> default is response template in `response_template.yaml` based on the action type of this entity.

    The default values of this field of different action types are as follows:

    UPDATE: `update_success` template in `response_template.yaml`.

    QUERY: `query_res` template in `response_template.yaml`.

    API: `api` template in `response_template.yaml`. (You'll probably mostly use this one. )

    INSERT: `insert` template in `response_template.yaml`.

    DELETE: `delete` template in `response_template.yaml`.

    INFORM: `inform_user` template in `response_template.yaml`.

    VERIFY: If the entity is verified, the default value is `okay` template in `response_template.yaml`. If verification fails, the default value is `ask_spelling` template or `cannot_recognize_entity` template in `response_template.yaml`.

    SIMPLE: No default value. If you leave this field empty, there will be no response after accepting this entity. For example, the entity is birthday and its action type is SIMPLE.

    ```
    birthday:
      response:
    ```

    Then the conversation will be like:

    > bot: May I know your birthday?

    > user: I was born on Jan 1, 1999.

    > bot: Where do you live?

    If you use `<info>` placeholder in this field, it will be replaced by the extracted value of this entity. If you change this field of this entity as:

    ```
    birthday:
      response:
        - Your birthday is <info>. Got it.
    ```

    Then the conversation will be like:

    > bot: May I know your birthday?

    > user: I was born on Jan 1, 1999.

    > bot: **Your birthday is Jan 1, 1999. Got it.** Where do you live?

    Usage 1 (if the response doesn't need the message returned by the entity function from the entity backend):

    Note that the `check_weather` function in the example takes the user's zip code as input and returns the weather. The action type of zip_code entity is API.

    ```
    check_the_weather:
        entities:
          zip_code:
            function: check_weather
            response:
              - Hmm. I made the `check_weather` function call to check the weather but I'm not able to tell you.
    ```

    > user: Could you please check the weather for me?

    > bot: Sure, could you please tell me the zip code of the area you want to check?

    > user: The zip code is 94301.

    > bot: **Hmm. I made the `check_weather` function call to check the weather but I'm not able to tell you.** Is there anything else I can help you with?

    Usage 2 (if the response needs the message returned by the entity function from the entity backend):

    Note that the `check_weather` function in the example takes the user's zip code as input and returns the weather. The action type of zip_code entity is API.

    ```
    check_the_weather:
        entities:
          zip_code:
            response:
              - One moment please. I think <info>.
    ```

    > user: Could you please check the weather for me?

    > bot: Sure, could you please tell me the zip code of the area you want to check?

    > user: The zip code is 94301.

    > bot: **One moment please. I think the weather in Palo Alto is sunny**. Is there anything else I can help you with?

  - `forget`: takes a boolean value and indicates whether to forget (erase) this entity after this task, so that in any subsequent tasks this entity will not be retrieved unless the user provides this entity again. → default is False

    ```
    check_the_weather:
        entities:
          zip_code:
            forget: True
    ```

    > user: Could you please check the weather for me?

    > bot: Sure, what is your zip code?

    > user: The zip code is 94301.

    > bot: Got it. The weather in Palo Alto is sunny. Is there anything else I can help you with?

    > user: I would like to check the order status.

    > bot: Sure, I’m happy to help you check the order status. **May I know your zip code?**

- `entity_groups`: A dictionary of lists of strings. The entities in the task can be grouped for better management. Each key in the dictionary is the alias of a group of entities. If you don’t want to group them, just simply stick with a single entity per group and set the alias the same as the entity name. For example in the following config, we have two groups, `Identity_related_entities` = [`username, email, shipping_address`] and `order_id` = [`order_id`], for the `verify_user` task. Here, `Identity_related_entities` and `order_id` are aliases to the corresponding entities; we will use these aliases in the `success` attribute. All the entities should be present in the entity.yaml file. In this case, it means to finish this task, we need to verify at least 2 entities in the `Identity_related_entities` entity group and all the entities in the `order_id` entity group.

  ```
  verify_user:
      entities:
        username:
          function: http://localhost:8001/verify_username
        email:
          function: http://localhost:8001/verify_email
        shipping_address:
          function: http://localhost:8001/verify_shipping_address
        order_id:
          function: http://localhost:8001/verify_order_id
      entity_groups:
        Identity_related_entities:
          - username
          - email
          - shipping_address
        order_id:
          - order_id
      success:
        AND:
          - VERIFY:
            - Identity_related_entities#2
          - VERIFY:
            - order_id
  ```

- `success`: stores a Task Tree that defines how to proceed with this task, i.e., procedures. The Task Tree is defined as follows

  - Each node of the tree can be either a logical value (AND / OR) or one of the possible action types (TASK, INFORM, VERIFY, UPDATE, DELETE, INSERT, QUERY, API, SIMPLE).
    - The most useful action types are TASK and API. TASK means the node is a task object, to go through the node the system needs to finish the task. API means to go through the node, the system needs to call an entity function in entity_functions.py or an external API.
    - SIMPLE means for the entities on this node (entities in this entity group), there will be no entity backend processing (a.k.a we don't need to do anything about this entity, we just store it in the entity module)
    - VERIFY, UPDATE, DELETE, INSERT, QUERY are database-related actions, and they're only for demo purposes, you may not want to use them.
    - If you put multiple entities in one entity group, they will have the same action type.
  - Each node has two conditions: successful or not successful. The default condition is not successful.
  - The procedure begins at the root node.
  - If the root node is successful, the task is successful.
  - If a node is a logical node, the system steps through its children nodes in order.
  - Nodes are called siblings if they share the same parent.
  - If a node is an AND node, all of its children nodes must be successful to proceed to the next node (i.e., its subsequent sibling node if there is any, or its parent node).
  - If a node is an OR node, only one of its children nodes must be successful to proceed to the next node (i.e., its subsequent sibling node if there is any, or its parent node).
  - Let’s start with a very simple example. In the above `verify_user` task, to verify a user, we need to verify **both** **all of the entities** in the `Identity_related_entities` entity group and **all of the entities** in the `order_id` group, then the success configuration of the verify user task should be like the following.

    ```
    verify_user:
      success:
        AND:
          - VERIFY:
            - Identity_related_entities
          - VERIFY:
            - order_id
    ```

  - In the above case, if the `Identity_related_entities` group is not verified, then the whole task will fail. The bot won’t continue verifying the `order_id` group.
  - By changing the AND to OR, the task’s procedure is changed to verify **either** all the entities in `Identity_related_entities` entity group or all the entities in `order_id` entity group. If either of the entity group is verified, the task is complete and considered successful.

    ```
    verify_user:
      success:
        OR:
          - VERIFY:
            - Identity_related_entities
          - VERIFY:
            - order_id
    ```

  - In the above case, if the `Identity_related_entities` group is not verified, the bot will continue verifying the `order_id` group. If the `order_id` group is verified, the task is considered successful, else the task will fail.
  - You may not necessarily use all the entities in an entity group. By simply adding a # following the entity group names, you can specify the number of entities to use in an entity group. In the following example, it means we need to verify **at least 2** of the entities in the `Identity_related_entities` entity group and all of the entities in the `order_id` group to finish this task.

    ```
    verify_user:
      success:
        AND:
          - VERIFY:
            - Identity_related_entities#2
          - VERIFY:
            - order_id
    ```

  - We can build **nested tasks** with the Task Tree. For example, if the bot is handling customer service for an e-commerce company, and the user wants to change the address of an order. The bot first needs to verify the user to locate the order in the database, then inform the user of the status of the order, and finally query the updated address. The success configuration of the above `change_address` task can be as follows. The task’s procedure is to first go through `verify_user` task (as **a sub-task**), and if successful, inform the user of order_status_related_entity (i.e., `order status`) and address_related_entity (i.e., `current address`), finally, ask for new_address and update it in the database(i.e., `updated_address`)

    ```
    change_address:
      entity_groups:
        order_status_related_entity:
          - order_status
        address_related_entity:
          - current_address
        new_address:
          - updated_address
      success:
        AND:
          - TASK:
            - verify_user
          - INFORM:
            - AND:
              - order_status_related_entity
              - address_related_entity
          - UPDATE:
            - new_address
    ```

  - Note that if a sub-task is successful, it won’t be repeated. The following is an example of a bot that can change the address and cancel an order. If the user already changed the address for an order, then suddenly wants to cancel it, the bot won’t verify the user again.

    ```
    verify_user:
      success:
        AND:
          - VERIFY:
            - Identity_related_entities#2
          - VERIFY:
            - order_id
    change_address:
      success:
        AND:
          - TASK:
            - verify_user
          - INFORM:
            - AND:
              - order_status_related_entity
              - address_related_entity
          - UPDATE:
            - new_address
    cancel_order:
      success:
        AND:
          - TASK:
            - verify_user
          - INFORM:
            - order_status_related_entity
    ```

  - Note that The Task Tree must not be cyclic (i.e., two tasks calling each other as a sub-task)

### FAQ/small-talk Configuration:

FAQ/small-talk is a one-turn dialogue that can happen anywhere in a conversation.

- `samples`: A _required_ field takes a list of strings that are the questions/the first half of the one-turn dialogue.
- `answers`: A _required_ field takes a list of strings that are the answers/the second half of the one-turn dialogue. One of the answers will be randomly selected and respond to the user.
- `question_match_options`: A _required_ field takes a list of strings value that indicates what method to use to match the FAQ samples. If `fuzzy_matching` is specified, the bot will use fuzzy matching to match the samples. If `nli` is specified, the bot will treat the FAQ as an intent and use the NLI model to match the samples together with other intent samples. The `fuzzy_matching` method is quicker than `nli` method, if you have a lot of FAQs, `fuzzy_matching` is recommended. If the `fuzzy_matching` result and the `nli` result have conflicts, the `nli` result will overwrite the fuzzy_matching result.

```
FAQ:
  learn_about_salesforce_AI_research:
    samples:
      - Could you tell me about Salesforce AI research team?
      - tell me about Salesforce AI research team
      - what projects does salesforce AI research team work on?
      - what projects are salesforce researchers working on?
      - I would like to know Salesforce research projects
    answers:
      - OK, here's what I found - https://einstein.ai/mission.
    question_match_options:
      - fuzzy_matching
      - nli
  job:
    samples:
      - where can I find job opportunities in Salesforce research?
    answers:
      - Thanks for your interest! Please see https://einstein.ai/career.
    question_match_options:
      - fuzzy_matching
  compliment:
    samples:
      - You are amazing!
    answers:
      - Thanks! I'm flattered:)
    question_match_options:
      - fuzzy_matching
```
