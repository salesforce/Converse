# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from typing import List
import logging

from Converse.config.config import (
    ConfigDictionaryOfType,
    FixedKeyConfigDictionary,
    ListOfStr,
    AllowedKeyConfigDictionary,
)
from Converse.utils.yaml_parser import (
    load_yaml,
    load_entity_extraction,
    get_entity_from_task_config,
)
from Converse.entity.entity import (
    # Entity classes
    Entity,
    CardinalEntity,
    DateEntity,
    EmailEntity,
    EventEntity,
    FacilityEntity,
    LanguageEntity,
    LawEntity,
    LocationEntity,
    MoneyEntity,
    NORPEntity,
    OrdinalEntity,
    OrganizationEntity,
    PercentEntity,
    PersonEntity,
    PhoneNumberEntity,
    PickListEntity,
    ProductEntity,
    QuantityEntity,
    StringEntity,
    TimeEntity,
    URLEntity,
    UserUttEntity,
    WorkOfArtEntity,
    ZipCodeEntity,
    # Entity extractors
    FuzzyMatchingEntityExtractor,
    NamedEntityExtractor,
    RegexMatchingEntityExtractor,
    SpellingEntityExtractor,
    UserUttExtractor,
)


log = logging.getLogger(__name__)


class EntityMethodConfig(AllowedKeyConfigDictionary):
    _AllowedKeys = {
        "ner",
        "spelling",
        "fuzzy_matching",
        "regex",
        "user_utterance",
    }


class EntitySpecification(FixedKeyConfigDictionary):
    _OPTIONAL_ATTRIBUTES = {
        "type": ListOfStr(),
        "methods": EntityMethodConfig(),
        "suggest_value": False,
    }

    def __init__(self, dictionary: dict):
        self.type = None
        self.methods = None

        super().__init__(dictionary)

        # we must make sure that each type is valid
        for entityType in self.type:
            if entityType not in EntityManager.type2class:
                raise ValueError("Invalid entity type: %s" % entityType)


class EntityConfig(ConfigDictionaryOfType):
    _type = EntitySpecification


class EntityManager:
    """
    Load in entity config file and extract appropriate entities for the
    current turn

    Attributes:
        type2class (dict): mapping of entity label to entity class
        entity_path (str): entity config file path
        entity_config (dict): entity config dictionary
    """

    type2class = {
        "CARDINAL": CardinalEntity,
        "DATE": DateEntity,
        "EMAIL": EmailEntity,
        "EVENT": EventEntity,
        "FAC": FacilityEntity,
        "LANGUAGE": LanguageEntity,
        "LAW": LawEntity,
        "AP/LOCATION": LocationEntity,
        "MONEY": MoneyEntity,
        "NORP": NORPEntity,
        "ORDINAL": OrdinalEntity,
        "ORG": OrganizationEntity,
        "PERCENT": PercentEntity,
        "PERSON": PersonEntity,
        "DUCKLING/phone-number": PhoneNumberEntity,
        "PICKLIST": PickListEntity,
        "PRODUCT": ProductEntity,
        "QUANTITY": QuantityEntity,
        "TIME": TimeEntity,
        "DUCKLING/url": URLEntity,
        "USER_UTT": UserUttEntity,
        "WORK_OF_ART": WorkOfArtEntity,
        "ZIPCODE": ZipCodeEntity,
        "STRING": StringEntity,
    }

    def __init__(
        self,
        entity_path="./Converse/bot_configs/entity_config.yaml",
        entity_extraction_path="./Converse/bot_configs/entity_extraction_config.yaml",
    ):
        self.entity_path = entity_path
        config_dict = load_yaml(self.entity_path)
        if "Entity" in config_dict:
            self.entity_config = config_dict["Entity"]
        elif "Task" in config_dict:
            self.entity_config = get_entity_from_task_config(config_dict["Task"])[
                "Entity"
            ]
        else:
            self.entity_config = dict()

        self.entity_extraction_path = entity_extraction_path
        self.entity_extraction_config = load_entity_extraction(
            self.entity_extraction_path
        )
        # Entity type value in the entity config should be a list of entity names
        # even if it only contains a single entity. Correct it if this is the case
        for entity_name, entity_dict in self.entity_config.items():
            if "type" not in entity_dict or isinstance(entity_dict["type"], list):
                continue
            entity_dict["type"] = [entity_dict["type"]]

        # load the entity config using EntityConfig
        self.entity_config = EntityConfig(self.entity_config)

    def _entity_class_from_label(self, label: str) -> type(Entity):
        """
        given an entity label, such as "EMAIL" or "CARDINAL", return its corresponding
        entity class, such as EmailEntity or CardinalEntity.
        will fall back to StringEntity if not present in type2class
        """
        try:
            return self.type2class[label]
        except KeyError:
            return StringEntity

    def get_entity_types(self, cur_entity_name: str) -> List[type(str)]:
        """
        obtain the currently expected entity types from the entity config
        return an empty list if nonexistent
        """
        entity_types = []
        try:
            entity_types = self.entity_config[cur_entity_name]["type"]
        except (TypeError, KeyError, AttributeError):
            log.info("no entity type provided for %s entity" % cur_entity_name)
        return entity_types

    def get_entity_classes(self, entity_name: str) -> List[type(Entity)]:
        """
        obtain the currently expected entity types from the entity config
        return an empty list if nonexistent
        """
        entity_classes = set()
        try:
            for label in self.entity_config[entity_name]["type"]:
                entity_classes.add(self._entity_class_from_label(label))
        except (KeyError, TypeError):
            log.info("no entity type provided for %s entity" % entity_name)
        return list(entity_classes)

    def get_extraction_methods(self, entity_name: str) -> dict:
        """
        Obtain extraction methods specified in the entity config yaml for the given
        entity name. If extraction methods are not defined for the given entity name,
        this function will use the entity types of the given entity to look up the
        default entity extraction methods in the entity extraction config.
        If the entity_name is invalid, such as None, it will return an empty dictionary
        """
        if not entity_name:
            return {}

        methods = self.entity_config[entity_name]["methods"]
        if not methods:
            methods = {}
            if entity_name:
                if entity_name in self.entity_config:
                    if (
                        "type" in self.entity_config[entity_name]
                        and self.entity_config[entity_name]["type"]
                    ):
                        for entity_type in self.entity_config[entity_name]["type"]:
                            methods.update(self.entity_extraction_config[entity_type])
                else:
                    raise KeyError(
                        "entity %s not defined in %s" % (entity_name, self.entity_path)
                    )

        return methods

    def suggest_entity_value(self, entity_name: str) -> bool:
        """
        Whether suggest entity values when the entity type is PICKLIST
        """
        if "suggest_value" in self.entity_config[
            entity_name
        ] and "PICKLIST" in self.get_entity_types(entity_name):
            return self.entity_config[entity_name]["suggest_value"]
        return False

    @staticmethod
    def extract_entities(
        utterance: str,
        methods: dict,
        ner_model_output: dict,
        entity_types: List[type(Entity)],
    ) -> List[Entity]:
        """
        Extract entities via methods provided
        Returned entities are NOT filtered by the entity_type

        entity_type is used only for spelling extraction method
        ner_model_output is used only for ner extraction method

        Entities are sorted by its score in the descending order
        """
        entities = []

        for method, value in methods.items():
            if method == "ner":
                entities.extend(
                    NamedEntityExtractor(ner_model_output).extract(utterance)
                )
            elif method == "spelling":
                # extract every spelling from each entity type
                for entity_type in entity_types:
                    entities.extend(
                        SpellingEntityExtractor(entity_type).extract(utterance)
                    )
            elif method == "fuzzy_matching":
                fuzzy_candidates = value
                entities.extend(
                    FuzzyMatchingEntityExtractor(fuzzy_candidates).extract(utterance)
                )
            elif method == "regex":
                pattern = value
                entities.extend(
                    RegexMatchingEntityExtractor(pattern).extract(utterance)
                )
            elif method == "user_utterance":
                entities.extend(UserUttExtractor().extract(utterance))

        # sort entities by its scores
        return sorted(entities, key=lambda x: x.score, reverse=True)


if __name__ == "__main__":
    pass
