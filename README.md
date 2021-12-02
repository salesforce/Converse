# Converse

Converse is a framework for designing task-oriented text and voice bots.

## Getting Started

### Requirements

- python >= 3.7

### Running the NLU (NER/Intent/Coreference) services
- Please check out [running NLU services in docker container](Converse/nlu/README_nlu.md)

### Running the Demo - Quick Start

If you don't plan to edit the package code, we recommend using this method of running Converse because it is easier.

1. Install [Docker](https://docs.docker.com/get-docker/).
2. Create a Python 3.7 virtual environment using [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) and activate it.
3. Run the following command to install the pip package of Converse:
   ```
   pip install -i https://test.pypi.org/pypi/ --extra-index-url https://pypi.org/simple converse-test-command==0.2.3
   ```
4. Install `svn` on your computer. On Mac, run:
   ```
   brew install svn
   ```
5. Run `converse-shell` to test if the package is successfully installed.
If the command line output contains "Hello, Converse!", then you installed the package successfully.
6. Run `converse-demo` to interact with pre-built example bots, and follow the instructions in your terminal.
Note that first-time users can leave every required input empty to use the default value.
Open the link provided by the script using your favorite browser, then you should see the demo page (pictured below).
You can interact with the bot by typing in the chat box on the right and the tree visualization will change based on 
your task progress.
![Picture of the demo in the browser](./pictures/demo_start.png)
![Picture of the demo in the browser after chatting with the bot](./pictures/demo.png)
7. Run `converse-build` to configure your own bot. Follow the instructions in the terminal to set up the bot.
Note that first-time users can leave every required input empty to use the default value.
Open the link provided by the script using your favorite browser, then you should see the configuration page
(pictured below). To learn more about how to build your own bot, please refer to
[guide for building your first bot](./documentation/Build_your_first_bot.md).
![Picture of the configuration tool](./documentation/pictures/5.png)

### Running the Demo After Modifying Files in Converse

1. Clone this repo and `cd` into the `eloq_dial` directory
    ```
    git clone git@github.com:MetaMind/eloq_dial.git
    cd eloq_dial
    ```
2. Create a Python 3.7 virtual environment using [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).
3. Install dependencies. All the necessary packages are listed in `requirements.txt`. You can install all the
   dependencies by running the following command:
    ```
    pip install -r requirements.txt
    ```
4. Add the `eloq_dial` folder to your `PYTHONPATH`.
   ```
   export PYTHONPATH=$PYTHONPATH:/your_directory/eloq_dial
   ```
5. In one terminal window, run the backend and check the log file converse.log:
    ```
    LOGLEVEL=[debug|info|warning|error|critical] python Converse/demo/dial_backend.py
    ```
   You may want to specify custom config files. Supply `--help` option to help you out. The default config files are
   listed in `orchestrator.py` file.
6. In a separate terminal window, run the entity backend services:
    ```
    python Converse/entity_backend/entity_service_backend.py
    ```
7. In a separate terminal window, run the front end and start interacting with the bot!
    ```
    python Converse/demo/client.py
    ```
   You can interact with the bot directly in the command line or in the browser by opening http://localhost:9002/client
   in your favorite browser.  To learn more about how to build your own bot, please refer to
   [guide for building your first bot](./documentation/Build_your_first_bot.md).

## Learn more about Converse

Please refer to the [tutorial on how to build your first bot](./documentation/Build_your_first_bot.md) to get started
by building your first bot.

To learn more about how to customize Converse for your use case, please refer to our documentation for each component of the system:
- [Task Configuration](./documentation/Task_Configuration.md)
- [Entity Configuration](./documentation/Entity.md)
- [Response Configuration](./documentation/Response_Configuration.md)
- [Policy Configuration](./documentation/Policy_config.md)
- [Information Layer Configuration](./documentation/Info_layer_config.md)

TODO - add a link to the paper and technical report

### More background information on dialogue management

Survey papers:

- [A Survey on Dialogue Systems: Recent Advances and New Frontiers](https://arxiv.org/pdf/1711.01731.pdf) - A survey
  paper on different components of dialogue systems and challenges of training and evaluating these systems.
- [Neural Approaches to Conversational AI (Chapter 4: Task-oriented Dialogue Systems)](https://arxiv.org/pdf/1809.08267.pdf)
  - A survey paper on different models in task-oriented dialogue systems.

## Terminology List

### Task Tree

An [And-Or Tree data structure](https://en.wikipedia.org/wiki/And%E2%80%93or_tree) that maintains structures and dependencies of the tasks that agent is currently
working on. \
See `dial_tree.py`.

### And Node

A task node or an **And** relation node in the Task Tree, corresponding to `AND` in `tasks.yaml`.

### Or Node

A task node or an **Or** relation node in the Task Tree, corresponding to `OR` in `tasks.yaml`.

### Leaf Node/ Entity Node

A node that maintains the information of an **entity group**, corresponding to groups like `entity_group_1` and `entity_group_2` in `tasks.yaml`.

### Leaf Node type

`INFO`, `VERIFY`, `UPDATE`, `DELETE`, `INSERT`, `QUERY`

### Entity

An entity, like `email_address`, `name`, etc.

### Entity configuration

`entity_config.yaml`, you can config entities in this file.

### Entity Type

For `NER` model and `spelling`, like `PERSON`, `CARDINAL`, `EMAIL`.

### Entity Method

The ways how we can extract entity information when `NER` doesn't work, like `SPELLING`, `GMAP`.

### Dialogue Tree Visualization

See `tree.html`, which loads `treeData.json` and shows a tree graph in browser.

### Dialogue Info Layer

Dialogue Info Layer makes API calls to NLU model services and collect model results. \
See `info_layer.py` and `info_logic.py` (old), which uses `info_layer.yaml` and `info_logic.yaml` (old) to config.

### Dialogue Policy Engine

Dialogue Policy Engine follows human-designed rules (which can be customized) to decide next Dialogue Action and
generate next Response based on information from Info Layer and Dialogue State Manager. \
The Dialogue Policy Engine is implemented in `dial_policy.py`, this is also the main script of the whole system. Config
file is `policy_config.yaml`. Responses are generated using functions in `response.py`. The text for the responses are
configured in `response_template.yaml`.

### Dialogue State Manager

Dialogue State Manager maintains all dialogue states. Dialogue states are all the information that the Dialogue Policy
Engine needs to generate the next response. It acts as a bridge between the Dialogue Policy Engine and the Dialogue Tree
Manager. The Dialogue Tree Manager decides the next node and next entity in dialogue tree for the current conversation
turn based on the task tree (configured in `tasks_yaml/tasks.yaml`) and information provided by the user in the last
turn. It interacts with `tree_manager.py` and `SimpleDB.py`. \
The Dialogue State Manager is implemented in `dial_state_manager.py`.
