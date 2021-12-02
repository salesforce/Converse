# Converse Entity Documentation

This document describes the entity module of Converse. This document assumes that you understand Python and have read `documentation/Build_your_first_bot.md`. After reading this document, you should be able to do the following:

* Understand how the entity manager extracts entities from user utterances.
* Understand how the entity history retrieves entities from past conversational turns.
* Configure entities for tasks.
* Add new entities and entity extractors.
* Define new entity functions and add entity functions to task configurations.

## What is an entity?

An entity is an object extracted from a user’s response that can be used to complete a task, for example the user’s zip code to help them check the weather in the area. We implemented entities as objects instead of using strings because structured objects are easier to manipulate than unstructured text. 

Entities have the following qualities: 
* A name
* An entity type
* Extraction methods
* A confidence score assigned by the extraction method

## How are entities used?

This section explains how Converse extracts entities from user utterances and retrieves entities from the conversational history.

### Extracting Entities from User Utterances

Extracting entities from user utterances is essential because Converse needs entities from users’ responses to help users complete tasks. 

After Converse asks the user for information that Converse needs to complete a task, the entity manager tries to extract the entity that Converse asked for from the user’s response. The following steps are the process for extracting entities from user utterances: 

1. The entity manager uses entity extraction methods defined in the entity configuration YAML file to extract entities from user utterances. 
2. After the entities are extracted, the entity manager sorts the entities by confidence scores produced by the entity extraction methods, and sends them to the dialogue policy. 
3. The dialogue policy filters the extracted entities to remove entities that have an entity type that don’t match the entity types defined in the entity configuration YAML file for the current entity expected for the task. 

### Retrieving Entities from Past Conversational Turns

The entity history enables Converse to reuse entities that the user previously provided in past conversational turns. The entity history also enables Converse to extract multiple entities from the same user input. 

When entity history retrieves entities from past conversational turns:

1. If the entity history contains an entity that has the same name as the current entity that the user confirmed was correct, then the entity history will return that entity. 
2. If the entity history doesn’t contain entities with the same name, the entity history retrieves entities that have a type that is in the list of entity types in the configuration for the current entity expected for the task, and sorts the list in descending order based on the confidence score of each entity. 

Please refer to the code in `Converse/entity/entity_history.py` for more details on the entity history.

The task configuration controls whether entities are saved in the history, whether they can be retrieved from history, and whether to confirm the entity when it is retrieved. See the task configuration documentation for more information and configuration instructions.

## Configuring Entities for Tasks

You can configure entities for tasks by creating an `entity_config.yaml` file such as the one below. The following sections will explain the purpose of each field in detail. 

```yaml
Entity:
  zip_code:
    type: ZIPCODE
    methods:
      ner:
      spelling:
```

### Entity Name

This section discusses the entity name, **zip_code** in the example below:

```yaml
Entity:
  zip_code:
    type: ZIPCODE
    methods:
      ner:
      spelling:
```

The entity name is a string that is the key that maps to the entity configuration dictionary that contains the entity types and extraction methods. The entity name should be unique. All entities used in the task configuration should have an entity configuration of the same name in the your entity configuration file. Entities can be shared between tasks, for example, two different tasks can use the same ZIP code entity `zip_code` configuration.

### `type`

This section discusses the **type** field, which is set to `ZIPCODE` in the example below:

```yaml
Entity:
  zip_code:
    type: ZIPCODE
    methods:
      ner:
      spelling:
```

This field stores the type or a list of types of the entity. The entity type depends on the kind of value that the entity holds, e.g. an email address or a date. Each entity type corresponds to a different Python entity class. 

Entities store a value that the entity extractors extracted from the user utterance and a score that represents the entity extractor confidence about extracting the entity correctly. Some entity classes normalize values to standardize how entities are stored, therefore making it easier to complete tasks, for example the normalized format of the `DATE` entity is a `datetime.date` object which makes it easier to compare the date with other dates or access different parts of the date such as the month or day. The value extracted from the user utterance or the normalized value needs to have the type of the value type of the entity, for example the value of a `CARDINAL` entity must be an `int` or `float`. 

#### **Special Configuration Cases**

This section describes special configuration cases that are not covered by the example above.

**How do you configure an entity with more than one entity type?**

If the entity has more than one entity type, the order that the entity types are listed in the configuration doesn’t matter. An example of an entity with more than one type is below. In this example, the location can be a `ZIPCODE` or an `AP/LOCATION` entity.

```yaml
Entity:
  location:
    type:
      - ZIPCODE
      - AP/LOCATION
    methods:
      ner:
      spelling:
```

**How do you configure an entity for an `INFORM` leaf node?**

If the entity is exclusively used under an `INFORM` leaf node in the `success` task configuration, then the type and methods fields can be left blank because Converse doesn’t use them. An example is below:

```yaml
Entity:
  address_of_store:
    type:
    methods:
```

**Using the optional `suggest_value` field in `PICKLIST` entities**

If the entity type is `PICKLIST`, then the entity configuration contains an optional `suggest_value` field that can be `true` or `false`. When the system asks the user for the `PICKLIST` entity and the `suggest_value` is `true`, the system will display all of the options under `fuzzy_matching` to the user. If `suggest_value` is false, then the system will not display the fuzzy matching options to the user. `suggest_value` is false by default. 

The following code is an example of a `PICKLIST` entity configuration with a `suggest_value` field:

```yaml
Entity:
  department:
    type: PICKLIST
    methods:
      fuzzy_matching:
        - ICU
        - Elderly services
        - Diagnostic Imaging
        - General Surgery
        - Neurology
        - Microbiology
        - Nutrition and Dietetics
    suggest_value: true
```

The dialogue using this entity will look something like this:


> Bot: Which department do you want to make the appointment with?
> Your choices are listed here:
> - ICU
> - Elderly services
> - Diagnostic Imaging
> - General Surgery
> - Neurology
> - Microbiology
> - Nutrition and Dietetics


You can change the “Your choices are listed here:” text by modifying the `suggest_entity_value` in `bot_configs/response_template.yaml`.

The following table shows the supported entity types and qualities of each entity type:

|Category	|Keyword (Use this as the entity type in the Entity YAML file)	|Entity Class (Defined in `Converse/entity/entity.py`)	|Supported Extraction Methods - Use this as the entity extraction methods in the Entity YAML file (The implementation of `ner` method is in parentheses)	|Description	|Value Type	|Normalized Value Format (Optional)	|
|---	|---	|---	|---	|---	|---	|---	|
|Cardinal number	|`CARDINAL`	|`CardinalEntity`	|`ner` (NER, Duckling)	|Numbers that don't fall under another type (e.g. 1, 2, one thousand)	|number (`int` or `float`)	|A number	|
|Date	|`DATE`	|`DateEntity`	|`ner` (NER, Duckling)	|Absolute or relative dates (e.g. yesterday, March 14, 3/14/15)	|string (`str`)	|A `datetime.date` object (e.g. March 14, 2015 is normalized as `datetime.date(2015, 3, 14)`)	|
|Email	|`EMAIL`	|`EmailEntity`	|`ner` (Duckling), `spelling`	|Email address (e.g. [example@example.com](mailto:example@example.com))	|string (`str`)	|-	|
|Event	|`EVENT`	|`EventEntity`	|`ner` (NER)	|Named hurricanes, battles, wars, sports events, etc.	|string (`str`)	|-	|
|Facility	|`FAC`	|`FacilityEntity`	|`ner` (NER)	|Buildings, airports, highways, bridges, etc.	|string (`str`)	|-	|
|Language	|`LANGUAGE`	|`LanguageEntity`	|`ner` (NER)	|Any named language (e.g. Spanish)	|string (`str`)	|-	|
|Law	|`LAW`	|`LawEntity`	|`ner` (NER)	|Named documents made into laws	|string (`str`)	|-	|
|Location	|`AP/LOCATION`	|`LocationEntity`	|`ner` (NER)	|Physical locations such as countries, cities, states, mountain ranges, and bodies of water	|string (`str`)	|If the location is a street address, then the normalized value is a tuple of tuples where the first entry is the name of the address part, and the second entry is the address part extracted from the user response (e.g. "123 Main Street, Palo Alto, CA 94020" is normalized as (("AddressNumber", "123"), ("StreetName", "Main"), ("StreetNamePostType", "Street,"), ("PlaceName", "Palo Alto,"), ("StateName", "CA"), ("ZipCode", "94020")).	|
|Money	|`MONEY`	|`MoneyEntity`	|`ner` (NER, Duckling)	|Monetary values, including the unit of measure (e.g. $10)	|string (`str`)	|A tuple containing two tuples. One tuple stores the monetary unit where the first entry is the string "unit" and the second entry is the string representing the monetary unit extracted from the user's response. The other tuple stores the amount of money where the first entry is the string "value", and the second entry is the amount of money extracted from the user's response as a floating point number. For example, "$50" is normalized as (("value", 50), ("unit", "$")).	|
|Nationalities or religious or political groups	|`NORP`	|`NORPEntity`	|`ner` (NER)	|Nationalities or religious or political groups (e.g. Americans)	|string (`str`)	|-	|
|Ordinal number	|`ORDINAL`	|`OrdinalEntity`	|`ner` (NER, Duckling)	|Ordinal numbers (e.g. “first”, “second”)	|string (`str`)	|An integer representing the ordinal number (e.g. "1st" is normalized as 1)	|
|Organization	|`ORG`	|`OrganizationEntity`	|`ner` (NER)	|Companies, agencies, institutions, etc. (e.g. Salesforce)	|string (`str`)	|-	|
|Percentage	|`PERCENT`	|`PercentEntity`	|`ner` (NER)	|Percentage (including “%”) (e.g. 40%)	|string (`str`)	|-	|
|Person	|`PERSON`	|`PersonEntity`	|`ner` (NER)	|People, including fictional (e.g. Sasha)	|string (`str`)	|-	|
|Phone Number	|`DUCKLING/phone-number`	|`PhoneNumberEntity`	|`ner` (Duckling)	|Telephone number	|string (`str`)	|A string representing the phone number where the country code is separated with parentheses (e.g. "+1 (650) 123-4567" is normalized as "(+1) 6501234567")	|
|Pick List	|`PICKLIST`	|`PickListEntity`	|`fuzzy_matching` (needs to be configured in the entity config)	|Uses fuzzy matching to match the user's response to a list of options defined by the bot builder and returns the closest match	|string (`str`)	|-	|
|Product	|`PRODUCT`	|`ProductEntity`	|`ner` (NER)	|Vehicles, weapons, foods, etc. (Not services)	|string (`str`)	|-	|
|Quantity	|`QUANTITY`	|`QuantityEntity`	|`ner` (NER)	|Measurements, as of weight or distance	|string (`str`)	|-	|
|Time	|`TIME`	|`TimeEntity`	|`ner` (NER, Duckling)	|Time durations or time of day (e.g. 2 pm)	|string (`str`)	|A `datetime.time` object (e.g. "1 pm" is normalized as `datetime.time(13, 0)`)	|
|URL	|`DUCKLING/url`	|`URLEntity`	|`ner` (NER)	|A URL web address	|string (`str`)	|-	|
|User Utterance	|`USER_UTT`	|`UserUttEntity`	|`user_utterance`	|The user's entire response	|string (`str`)	|-	|
|Work of Art	|`WORK_OF_ART`	|`WorkOfArtEntity`	|`ner` (NER)	|Titles of books, songs, etc.	|string (`str`)	|-	|
|ZIP Code	|`ZIPCODE`	|`ZipCodeEntity`	|`ner` (NER), `spelling`	|5-digit number representing postal codes in the United States. This entity checks that the number has 5 digits but does not check if the number is a valid ZIP code.	|string (`str`)	|-	|
|String	|`STRING`	|`StringEntity`	|`ner` (NER - only outputs this type if the label doesn't match any other label), `regex` (Regular expressions - needs to be configured in the entity config)	|Default entity type that is returned if the NER entity extractor doesn't support the label of the entity extracted from the user response.	|string (`str`)	|-	|

### `methods`
This section discusses the **methods** field, which is set to `ner` and `spelling` in the example below:
```yaml
Entity:
  zip_code:
    type: ZIPCODE
    methods:
      ner:
      spelling:
```

This field stores the extraction methods that Converse uses to extract entities from the user utterance. The order that the extraction methods are listed in the configuration doesn’t matter. If the methods dictionary is empty, then Converse will use the default entity extraction methods for the entity types of the entity defined in `Converse/bot_configs/entity_extraction_config.yaml`. 

The following table lists the supported entity extraction methods and examples of how to configure them:

<table>
    <tr>
        <td>Method</td>
        <td>Keyword  (use this as the entity extraction methods in the Entity YAML file)</td>
        <td>Entity Extractor Class (Defined in <code>Converse/entity/entity.py</code>)</td>
        <td>Description</td>
        <td>Example Configuration</td>
    </tr>
    <tr>
        <td>Named Entities</td>
        <td><code>ner</code></td>
        <td><code>NamedEntityExtractor</code></td>
        <td>This extractor extracts entities using a named entity recognition model and Duckling, a rule-based library that parses text into structured data. This is the most commonly used extractor in Converse. All entities that implement the <code>from_ner_model</code> method support NER.</td>
        <td>
            <pre lang="yaml">
birthday:
  type: DATE
  methods:
    ner:
            </pre>
        </td>
    </tr>
    <tr>
        <td>User Utterance</td>
        <td><code>user_utterance</code></td>
        <td><code>UserUttExtractor</code></td>
        <td>This extractor stores the entire user utterance as the entity's value. This entity extractor only supports user utterance <code>USER_UTT</code> entities.</td>
        <td>
            <pre lang="yaml">
have_health_insurance:
  type: USER_UTT
  methods:
    user_utterance:
            </pre>
        </td>
    </tr>
    <tr>
        <td>Spelling</td>
        <td><code>spelling</code></td>
        <td><code>SpellingEntityExtractor</code></td>
        <td>This extractor extracts entities when the user spells out entity information letter by letter, e.g. "J A S O N" for "Jason". This extractor is meant to be used for voice calls. All entities that implement the <code>from_spelling</code> method support extraction using spelling.</td>
        <td>
            <pre lang="yaml">
name:
  type: PERSON
  methods:
    ner:
    spelling:            
            </pre>
        </td>
    </tr>
    <tr>
        <td>Fuzzy Matching</td>
        <td><code>fuzzy_matching</code></td>
        <td><code>FuzzyMatchingEntityExtractor</code></td>
        <td>This extractor extracts entities using fuzzy matching by comparing the user utterance with a list of candidates and returning the best matches. The list of candidates is configured in a list under <code>fuzzy_matching</code>, such as the list of medical departments in the example on the right. This entity extractor only supports pick list <code>PICKLIST</code> entities.</td>
        <td>
            <pre lang="yaml">
department:
  type: PICKLIST
  methods:
    fuzzy_matching:
      - ICU
      - Elderly services
      - Diagnostic Imaging
      - General Surgery
      - Neurology
      - Microbiology
      - Nutrition and Dietetics
  suggest_value: true            
            </pre>
        </td>
    </tr>
    <tr>
        <td>Regular Expressions</td>
        <td><code>regex</code></td>
        <td><code>RegexMatchingEntityExtractor</code></td>
        <td>This extractor extracts entities by finding all matches with a regular expression pattern. If there is more than one match, this extractor will return all of them. This pattern is configured as the value for the `regex` dictionary in the configuration, such as the regex pattern <code>\d{7}</code> that matches strings with seven digits to extract the application number in the example on the right. This entity extractor only supports <code>STRING</code> entities.</td>
        <td>
            <pre lang="yaml">
application_number:
  type: STRING
  methods:
    regex: \d{7}
            </pre>
        </td>
    </tr>
</table>

## Adding New Entities and Entity Extractors (A Feature for Advanced Users)

Since Converse already supports many entity types and entity extractors, adding new entities and entity extractors is only necessary in a few cases, such as when you add a new label to your NER model or want to apply a new way of extracting entities from user utterances.

The following customizations are only supported if you build Converse from source.

### Adding a New Entity Class

You might want to add a new entity class for the following reasons:

* You want to add a new label to your NER model and create a new entity class to represent this label.
* You want to add more rules to check the value of entities, such as checking that the value is a five digit number before creating a `ZIPCODE` entity.
* You want to customize how the entity normalizes the value, such as representing a date as a Python date object.

If you want to add a new entity class, then you need to make the following modifications to `Converse/entity/entity.py`. 

* Create a new entity class in  `Converse/entity/entity.py` by extending the `StringEntity` or `NumberEntity` class. If your new entity has a string `str` value type, extend the `StringEntity` class. If your new entity has an integer `int` or a floating point `float` value type, extend the `NumberEntity` class. These base entity classes check that the value stored in the entity matches these expected value types.
* If the entity has a normalized value, override the `display_value` method that converts the normalized value into a human readable version of the value. If you don’t override this method, `display_value` will return the normalized value casted as a string.
* If the entity can be extracted using NER, override the `from_ner_model` class method that converts the NER output dictionary into an entity object. You also need to update the dictionary that maps NER labels to entity objects, `label2type`, in the named entity extractor class `NamedEntityExtractor` to output your new entity.
* If the entity can be extracted using spelling, override the `from_spelling` class method that converts the user utterance with spelled out words into an entity object. The spelling extractor class `SpellingEntityExtractor` calls the `from_spelling` method to extract entities using spelling.

After you add your new entity class to `Converse/entity/entity.py`:

* Add the new keyword that you will use in the entity configuration YAML files to the dictionary that maps keywords to Entity classes, `type2class` in the entity manager class `EntityManager` in `Converse/entity/entity_manager.py`.
* If you plan to use your new entity often and don’t want to define the entity extraction method every time in entity configuration files, add a default entity extraction method in `Converse/bot_configs/entity_extraction_config.yaml` for your new entity. 

### Adding a New Entity Extractor Class

You might want to add a new entity extractor class for the following reasons:

* You want to add a new method for extracting entities from user utterances.
* You want to extend an existing entity extractor class to cover more cases, such as making the fuzzy matching entity extractor output a custom entity class.

Make the following changes to `Converse/entity/entity.py` to add a new entity extractor:

* Create a new entity extractor class by extending the `EntityExtractor` object.
* Add an `__init__` method if the entity extractor needs additional information to extract entities, for example, the regular expression extractor needs a regular expression pattern that it uses to extract entities.
* Override the `extract` method that extracts entities from a user utterance and returns a list of extracted entities.
* Add your new entity extraction method to the extraction method enum `ExtractionMethod`. This enum specifies the extraction method in the entity object.

You also need to make the following changes to `Converse/entity/entity_manager.py`:

* Add the keyword for your new entity extractor to the entity method configuration enum `EntityMethodConfig` that checks if the values in the entity configuration YAML match the expected types.
* Add your entity extraction method to the `extract_entities` method in the entity manager `EntityManager` class that extracts entities from all user utterances.

## Entity Functions

Entity functions are Python functions or RESTful APIs that process entities during tasks. Entity functions can be used to call APIs outside of Converse, such as using the date and time collected from the user during the conversation to call the Google Calendar API to create a calendar invitation. You can associate entity functions with tasks by configuring the `Entity` section of the task configuration YAML file. Examples of entity functions and task configurations are in the subsections.

### Defining Entity Functions That Are Python Functions

An example of an entity function from `Converse/entity_backend/entity_functions.py`  is below. `Converse/entity_backend/entity_functions.py`  contains all built-in entity functions that are Python functions. The entity function in the example converts inches to centimeters.

```python
@timeout(0.1)
def funcInch2Cm(entities, *argv, **kargs):
    entity_name = "inch"
    inch = float(entities[entity_name])
    cm = 2.54 * inch
    return resp(True, "{} inch equals to {} centimeter".format(inch, cm))
```

Every entity function has the same function signature as the function above: it takes the current entities and additional positional and keyword arguments as input, and outputs a user response. You will use the function name to specify the entity function in the task configuration. The input `entities` is a dictionary containing all the entities provided by the user for the current task. The current dialog states are inputted as keyword arguments to the function. The output of the function is a call to the `Converse.utils.utils.resp`  function with a boolean representing whether the function completed successfully and a string that will be displayed to the user. The `timeout` decorator on the function specifies how many seconds to wait before the function times out.

An example of a task and entity configuration that uses `funcInch2Cm` is below in the `function` field.

```yaml
Task:
  convert_inch_to_cm:
    description: convert inch to centimeter
    samples:
      - I want to convert inch to centimeter
      - convert inch
      - inch to cm
    entities:
      inch:
        confirm: no
        retrieve: False
        function: funcInch2Cm
        prompt:
        response:
    entity_groups:
      entity_group_1:
        - inch
    success:
      AND:
        - API:
            - entity_group_1
    repeat: False
    max_turns: 10
```
```yaml
Entity:
  inch:
    type: CARDINAL
    methods:
      ner:
      spelling:
```

To add your own entity functions, you can create a new Python file with entity functions and pass the file path as input to the `entity_function_path` argument of the `Orchestrator` class like the example below:

```python
orchestrator = Orchestrator(
    task_path="your_tasks.yaml",
    entity_path="your_entity_config.yaml",
    entity_function_path="your_additional_entity_function.py",
)
```

### Defining Entity Functions That Are RESTful APIs

An example of an entity function defined as a RESTful API is below. This function converts inches to centimeters (just like the example above). This example is from `Converse/entity_backend/service_backend.py`, which contains more entity function REST API examples. 

```python
@timeout(0.1)
@app.route("/inch_2_cm", methods=["POST"])
def funcInch2Cm():
    dm_msg = request.json
    entity_name = "inch"
    inch = float(dm_msg[entity_name])
    cm = 2.54 * inch
    return json_resp(True, "{} inch equals to {} centimeter".format(inch, cm))
```

The entity function above has different inputs and outputs than the entity functions that are Python functions. The entity function takes no arguments as input. Instead, the entities are passed as a part of the POST request. The output is a call to the `json_resp` function where the first argument is a boolean that represents whether the function completes successfully and the second argument is the message to display to the user. The `timeout` decorator specifies how long to wait before the function times out. The `app.route` decorator specifies the API endpoint path and REST API type POST. You will use the API endpoint path to specify the entity function in the task configuration.

This example uses Flask to host the backend endpoint. However, you can select any architecture as long as it returns a dictionary where:

* the “success” key maps to a boolean that is true when the API completes successfully, and false otherwise
* the “msg” key maps to a message to display to the user


An example of a task and entity configuration that uses the REST API for `funcInch2Cm` is below. The reference to the API is in the `function` section.

```yaml
Task:
  convert_inch_to_cm:
    description: convert inch to centimeter
    samples:
      - I want to convert inch to centimeter
      - convert inch
      - inch to cm
    entities:
      inch:
        confirm: no
        retrieve: False
        function: http://localhost:8001/inch_2_cm
        prompt:
        response:
    entity_groups:
      entity_group_1:
        - inch
    success:
      AND:
        - API:
            - entity_group_1
    repeat: False
    max_turns: 10
```
```yaml
Entity:
  inch:
    type: CARDINAL
    methods:
      ner:
      spelling:
```

### Learn more about how entity functions are integrated

To learn more about how the dialogue state manager calls entity functions, please refer to the function `_execute_entity_or_task_function` in `Converse/dial_state_manager/dial_state_manager.py`.

