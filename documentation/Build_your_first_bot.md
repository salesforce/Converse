# Build your first bot with Converse

## Start the NLU services first
```
docker run --name myintent -p 9001:9001 converseallresearch/intent:0.1
docker run --name myner -p 50051:50051 converseallresearch/ner:0.1
```
## Two ways to make a new bot from scratch

### 1. Writing config yaml files:

There are two YAML files you need to mainly care about when you are creating a new bot. One is the Task YAML file and the other is the Entity YAML file. The Task YAML file contains task-related configuration items. The Entity YAML file contains configuration items for entity extraction.
You can refer to ... to get the details about those two files.
Note that, the entities in Entity YAML file are shared by all the tasks in Task YAML file. If you are using an entity (like ZIP code) in different tasks, it will follow the same entity extraction setting specified in Entity YAML file. Alternatively, you can merge Task YAML file and Entity YAML file into one file by moving the entity extraction settings to the `entities` sections in Task YAML file. If you merge the two files, the task configuration file path and entity configuration file path should be the same when you are running the bot.

OK. Let’s go back to the generated Task and Entity YAML files.  Let’s start with creating a bot to convert inches to centimeters.  
**Step 1: Create empty task and entity YAML files templates**:

```
python Converse/utils/config_yaml_generator.py
```

When you create the yaml files, you will input the bot name, task names and entity names interactively in the terminal like the example below. 

```
Input yaml dir, default is Converse/bot_configs: Converse/bot_configs/example_bot_in_tutorial
Input bot name : demo bot
Input a task name: inch_to_cm
Input entity names (entity_1||entity_2||entity_3): inch
Continue adding tasks? (Input yes or no): no
Do you want to also add FAQs? (Input yes or no): no
```

The generated Task YAML file should look like this:

```
Bot:
  text_bot: true
  bot_name: demo bot
Task:
  positive:
    description: polarity
    samples:
    - 'Yes'
    - Sure
    - correct
    - No problem
    - that's right
    - yes please
    - affirmative
    - roger that
  negative:
    description: polarity
    samples:
    - 'No'
    - Sorry
    - No, I don't think so.
    - I dont know
    - It's not right
    - Not exactly
    - Nothing to do
    - I forgot my
    - I forgot it
    - I don't want to tell you
  inch_to_cm:
    description: null
    samples: []
    entities:
      inch:
        function: null
        confirm: false
        prompt: []
        response: []
    entity_groups:
      entity_group_1: []
    success:
      AND: []
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    `task_finish_function: null`
    max_turns: 10
```

The `positive` and `negative` tasks are generated automatically: you don’t need to make any changes to them. They are used for polarity detection, which is important for confirming information with users. 

**Step 2: Add necessary things to the empty task YAML files templates**:
Let’s add necessary things to the `inch_to_cm` task. You can refer to Task configuration documentation to get the full details.
For each task, the necessary fields you need to fill are:

* `description`: a required field that is a string that describes what the task is about.
* `samples`: a list of strings that are used to detect the task from the user utterances, usually 3 to 5 sentences. Leave the field empty when you don’t want a task to be triggered by any user utterances. 
* `entities`:
    * `function` is a function name or a URL of a RESTful API. Here, `funcInch2Cm` is a function we defined in `Converse/entity_backend/entity_functions.py` . You can add your own entity functions in the same file.
    * `confirm` is a boolean value to indicate whether or not the system should verify the collected entity info with the user before further processing. 
    * `prompt` is a list of strings used to prompt the user when the bot asks for this entity. 
    * `response` is a list of strings used to prompt the user after this entity is successfully processed.
    * `prompt` and `response` can be empty. There are default prompt and response sentences.
* `entity_groups`:
    * You can put entities in several entity groups. The entity groups will be used in the `success` section. For simplicity, you can stick with a single entity per group.
* `success` defines the And-Or task tree structure. 
* `finish_response`, `repeat, repeat_response`, `task_finish_function` are optional.

 
After filling out these fields, the `inch_to_cm` section in the above Task YAML file should look like this:

```
inch_to_cm:
    description: convert inches to centimeters
    samples: 
      - I want to convert inch to centimeter
      - can you help me convert inch to centimeter
      - inch to centimeter
      - convert inch
    entities:
      inch:
        function: funcInch2Cm
        confirm: false
        prompt:
         - How many inches do you want to convert?
        response:[]
    entity_groups:
      entity_group_1: 
       - inch
    success:
      AND: 
       - API:
          - entity_group_1
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
```

**Step 3: Add necessary things to the empty entity YAML files templates**
The generated Entity YAML file should look like this:

```
Entity:
  inch:
    type: null
    methods: {} 
```

We need to specify the `type` of the entity, and the `methods` to extract the entity values from the user utterance.

We can use regular expressions to extract the number we want. Let’s change the default Entity YAML file like the following:

```
Entity:
  inch:
    type: STRING
    methods:
      regex: '\d+\.?\d*'
```

Sometimes, one entity can have multiple types. If we want to use both regular expressions and NER to extract the number, we can change the config to:

```
Entity:
  inch:
    type: 
      - STRING
      - CARDINAL
    methods:
      regex: '\d+\.?\d*'
      ner:
```

**Step 4: Run the bot!**
Now, let’s run our bot!

```
python Converse/demo/dial_backend.py --task_path Converse/bot_configs/example_bot_in_tutorial/tasks.yaml --entity_path Converse/bot_configs/example_bot_in_tutorial/entity_config.yaml
```

By default, the backend is running on  [http://0.0.0.0:9002/](http://0.0.0.0:9002/client). You can open your browser, and then go to http://0.0.0.0:9002/client
You can see the chat page. In the beginning, no task is triggered. The task tree only has one root node.
![1](pictures/1.png)
Let’s talk with the bot! It works!
![2](pictures/2.png)
**Step 5: Test and iterate (optional)**
What if I want to add more rules for the `inch_to_cm` task? Somehow, I want the bot to first complete a subtask, which is verifying the user’s identity before convert inch to centimeter.

```
python Converse/utils/config_yaml_generator.py
```

```
Input yaml dir, default is Converse/bot_configs: Converse/bot_configs/example_bot_in_tutorial
Input bot name: demo bot
Input a task name: verify_user
Input entity names (entity_1||entity_2||entity_3): name
Continue adding tasks? (Input yes or no): no
Do you want to also add FAQs? (Input yes or no): no
```

You can see this was added to the Task YAML file.

```
verify_user:
    description: null
    samples: []
    entities:
      name:
        function: null
        confirm: false
        prompt: []
        response: []
    entity_groups:
      entity_group_1: []
    success:
      AND: []
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
```

Then we can complete the new task’s configuration. 

```
verify_user:
    description: verify your identity
    samples: []
    entities:
      name:
        function: null
        confirm: false
        prompt: []
        response: []
    entity_groups:
      entity_group_1:
        - name
    success:
      AND:
        - SIMPLE:
            - entity_group_1
    finish_response:
      success:
        - I have verified your identity.
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
```

Don’t forget to add the new entity name to the Entity YAML file.

```
Entity:
  inch:
    type: STRING
    methods:
      regex: \d+\.?\d*
  name:
    type: PERSON
    methods:
      ner: null  
```

Let’s change the `success` condition of `inch_to_cm` task.
When `inch_to_cm` is triggered, the bot will first complete a subtask, which is `verify_user`. 
This time we also enable `repeat`. The bot will ask the user whether to do the task again.

```
inch_to_cm:
    description: convert inches to centimeters
    samples:
    - I want to convert inch to centimeter
    - can you help me convert inch to centimeter
    - inch to centimeter
    - convert inch
    entities:
      inch:
        function: funcInch2Cm
        confirm: false
        prompt:
        - How many inches do you want to convert?
        response: []
    entity_groups:
      entity_group_1:
      - inch
    success:
      AND:
      - TASK:
        - verify_user
      - API:
        - entity_group_1
    finish_response:
      success: []
      failure: []
    repeat: true
    repeat_response: 
      - Do you want to convert inch to centimeter again?
    task_finish_function: null
    max_turns: 10
```

Let’s try the new bot now! 
Stop the previous `dial_backend` service. Then run it again:

```
python Converse/demo/dial_backend.py --task_path Converse/bot_configs/example_bot_in_tutorial/tasks.yaml —entity_path Converse/bot_configs/examlple_bot_in_tutorial/entity_config.yaml
```

open http://0.0.0.0:9002/client
You can see that the bot is capable of two different tasks, and one task depends on the other one. The subtask will not repeat after completed.
![3](pictures/3.png)
Now, I believe that you can build a very simple bot with **Converse**. We provided several template bots. You can look at them to understand the system better.

### 2. Using config UI tool:

We also provide a config UI tool to help you build your bot. The config UI generates a merged task and entity YAML file. Note that the upload button in the config UI is for resetting merged task-entity yaml file template. The default template file is `./Converse/demo/static/yamls/merged_task_entity.yaml.tmpl`. You can click download button to get the current saved merged task-entity config yaml file.

Run `run_config_UI.sh` to start config UI tool. 
Open http://0.0.0.0:8080/?file=task in your browser, and you can see the config UI like this. Select `reset` next to `task` in the bottom left corner.
![5](pictures/5.png)
Now let’s begin to build a new bot. Input the `bot_name` first.
![6](pictures/6.png)
Then click `Next` in the bottom right corner. Click `New Task` in the bottom right corner.
![7](pictures/7.png)
There are tooltips in the UI in case you are not familiar with some keys in bot configuration.
![8](pictures/8.png)
Click `Next`, and then click `Yes`.
![9](pictures/9.png)
Click `New entities`.
![10](pictures/10.png)
The `entity functions` in `Converse/entity_backend.py/entity_functions.py` are listed in the UI.
![11](pictures/11.png)
Choose STRING as the entity type.
![12](pictures/12.png)
Click `Next`, then click `Yes`.
![13](pictures/13.png)
Click `+` in the top-right corner, select `regex` and click `Add`.
![14](pictures/14.png)
Input the regular expression under `regex` for extracting float numbers. Click `Next`. 
Some methods don’t require any further input, such as `ner`, `spelling,` and `user_utterance`,  you can leave the field empty after selecting those methods.
![15](pictures/15.png)
Click `Yes` to create entity `groups`.
![16](pictures/16.png)
Then we add `entity_group_1`. Click `+` in the top-right corner.
![17](pictures/17.png)
Select `inch`.
![18](pictures/18.png)
You can also change the entity group names after you added them.
![35](pictures/35.png)
Click `Next`.
![19](pictures/19.png)
Click `Yes`.
![20](pictures/20.png)
Click `Next`.
![21](pictures/21.png)
Click `Yes`.
![22](pictures/22.png)
We can finish this later. Let’s add another task.
![23](pictures/23.png)
Go back to `Task` and click `New Task`.
![24](pictures/24.png)
Add `verify_user` task.
![25](pictures/25.png)
Add entity `name` for `verify_user` task.
![26](pictures/26.png)
We use `ner` as the entity extraction method.
![27](pictures/27.png)
Add `entity group` for `verify_user` task.
![28](pictures/28.png)
Add `finish_response` for `verify_user` task.
![29](pictures/29.png)
The task tree structure of `verify_user` task is
![30](pictures/30.png)
Now go back to `success` condition of `inch_to_cm`, and add the task tree structure.
![31](pictures/31.png)
Now click `save`. The generated yaml file is `Converse/demo/static/yamls/merged_task_entity.yaml`
![32](pictures/32.png)
Click `chat` .
![33](pictures/33.png)
Click `reset` button in the top-right corner first, then you can use your bot!
![34](pictures/34.png)
