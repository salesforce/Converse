let tooltips = {
    '["__Bot"]': {'name': 'The task config yaml file should first begin with a single key Task, whose value are again dictionaries of config for every task it supports.'},
    '["Bot"]':{
        'bot_name': 'you can give the bot a name',
        'text_bot': 'False means the bot is a voice bot, which takes the output text from a speech recognition model. True means the bot takes the text directly, without any preprocessing modules. You can just set this to True.'
    },
    '["Task","_name_"]': {
        'name': 'the name of the task',
        'description': 'a required field taking a string value, describing what the task is about',
        'samples': 'taking a list of strings that are used to detect the task from the user response',
        'repeat': 'taking a boolean value whether or not to repeat this task after success (i.e., prompt the user to repeat this task), default is False',
        'repeat_response': 'taking a list of strings that are used as prompt sentences for repeating the task (like "Do you want to do this task again?")',
        'max_turns': 'taking a numeric value indicating the maximum allowed turns for this task to complete',
        "task_finish_function": 'process all the collected entity information after successfully complete a task using this Python function or the URL of an external RESTful API',
    },
    '["Task","_name_","finish_response"]': {'name': 'response to the user after completing this task. It takes a dictionary of a list of string with keys success and failure. One of the corresponding responses will be randomly selected and output to the user.'},
    '["Task","_name_","entity_groups"]': {'name': 'it defines groups of entities that we are interested in with its alias. For simplicity, you can stick with a single entity per group. We will use these aliases in success attribute below.'},
    '["Task","_name_","entities","_name_"]': {
        'name': 'the name of the entity that associated with the current task',
        'function': 'the Python function name or the URL of an external RESTful API to process the collected entity info',
        'prompt': 'takes a list of strings to prompt to the user when asking for this entity',
        'response': 'takes a list of strings to be prompted to the user after this entity is successfully processed',
        'confirm': 'takes a boolean value to indicate whether or not the system should verify the collected entity info with the user before further processing',
        'retrieve': 'takes a boolean value whether or not to retrieve this entity from the user’s input in the previous turns',
        'forget': 'takes a boolean value and indicates whether to forget (erase) this entity after this task, so that the entity info will not be retrieved, unless the user provides this entity again',
        'suggest_value': "used only for PICKLIST entity type. If it is True, Converse will let users know the possible choices from the picklist before asking user to choose. If it is False, Converse will ask for user's choice directly",
        'type': 'this field defines the type of the entity, which is used for slot filling'
    },
    '["Task","_name_","entities","_name_","methods"]': {
        'name': 'a dictionary of entity extraction methods that Converse will use to extract entities from the user utterance',
        'ner': 'extract entity info using Named-entity recognition model',
        'regex': 'extract entity info using regular expression you defined',
        'spelling': 'extract entity info using rule-based spelling method, like test at salesforce dot com -> test@salesforce.com',
        'user_utterance': 'use the whole user input as the extracted entity info (this useful when you need to bypass the default entity extraction methods)',
        'fuzzy_matching': 'you can provide a candidate picklist, the entity will be selected from the picklist using fuzzy matching'
    },
    '["Task","_name_","success"]': {'name': 'takes a Task Tree that defines how to proceed with this task'},
    'xxx': {'name': 'xxx'},
};
