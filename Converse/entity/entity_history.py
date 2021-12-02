# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

from typing import List
from collections import defaultdict

from Converse.entity.entity import Entity, UserUttEntity, PickListEntity


class EntityHistoryManager(object):
    """
    stores entities observed during the dialog
    """

    def __init__(self):
        """
        Attributes:
          history (dict): { turn: set[entity] }
          named_entity (dict): {entityname: Entity}
        """
        self.history = defaultdict(set)
        self.named_entity = defaultdict(Entity)

    def reset(self):
        """
        clear away all history
        """
        self.history.clear()
        self.named_entity.clear()

    def insert(self, entity: Entity, turn: int):
        """
        insert a new entity with its associated turn
        """
        assert isinstance(entity, Entity) and isinstance(turn, int)
        if not isinstance(entity, UserUttEntity):
            self.history[turn].add(entity)

    def insert_named_entity(self, name: str, entity: Entity):
        """
        A named entity is expected to be a reliable, confirmed entity as a fast track.
        We expect a 1 to 1 mapping. It will overwrite the existing entity if called
        with an existing entity name
        """
        self.named_entity[name] = entity

    def retrieve(
        self,
        entity_type: type(Entity),
        turns: List[int] = None,
        entity_name: str = None,
    ) -> List[Entity]:
        """
        entity_name acts as a fast track. That is, it will retrieve the named entity
         and return if exits. If not, it will retrieve unique entities of the given
         entity_type at given turns. If no turn is provided, it will retrieve entities
         from all available turns
        """

        if entity_name in self.named_entity:
            entity = self.named_entity[entity_name]
            if type(entity) == entity_type:
                return [entity]

        turns = self.history.keys() if not turns else turns

        # grab all entities belonging to the specified turns
        entities_by_turn = set()
        for turn in turns:
            for entity in self.history[turn]:
                if type(entity) == entity_type:
                    if isinstance(entity, PickListEntity) or isinstance(
                        entity, UserUttEntity
                    ):
                        continue
                    entities_by_turn.add(entity)

        # create a dictionary of (value, entity)
        # so that we can get entities of unique values with the highest score
        entities = Entity.unique(entities_by_turn)

        # return a list of values in descending order of score
        return sorted(entities, key=lambda x: x.score, reverse=True)

    def remove(self, entity: Entity):
        """
        Remove any entity that has the same value or user utterance value as the passed
        entity, regardless of its type. When we compare the values, we type-cast to
        make sure that entities of different types are also removed if they have the
        same type-cast values
        """
        # check every turn and remove the entity
        for _, entities in self.history.items():
            to_remove = []
            for e in entities:
                value_types = (entity.value_types,)
                if isinstance(entity.value_types, tuple):
                    value_types = entity.value_types
                for value_type in value_types:
                    try:
                        # we need to convert the entity value to the target value type.
                        # Entity extractor may provide multiple entities of different
                        # types.
                        # Ex) We may have CardinalEntity of int 94301,
                        # and ZipCodeEntity of str '94301', all derived from a single
                        # utterance.
                        # We need to make sure to remove ALL of these.
                        value = value_type(e.value)
                    except Exception:
                        # if type conversion is incompatible,
                        # then they are obviously not a match
                        continue
                    if entity.value == value or (
                        str(entity.user_utt_value) == str(e.user_utt_value)
                    ):
                        to_remove.append(e)
                        break
            for e in to_remove:
                entities.remove(e)

    def remove_named_entity(self, name: str):
        """
        Remove the named entity if exists
        The caller is expected to call `remove` function as well if necessary
        This is analogous to how the caller must call both
        `insert` and `insert_named_entity`
        """
        if name in self.named_entity:
            del self.named_entity[name]


if __name__ == "__main__":
    from Converse.entity.entity import EmailEntity, StringEntity, ExtractionMethod

    email_entity = EmailEntity(1, ExtractionMethod.NER, "peter@hotmail.com")
    manager = EntityHistoryManager()
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)

    email_entity = EmailEntity(1, ExtractionMethod.SPELLING, "peter@hotmail.com")
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)

    email_entity = EmailEntity(0.5, ExtractionMethod.FUZZY_LOGIC, "peter@hotmail.com")
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)
    manager.insert(email_entity, 1)

    string_entity = StringEntity(1, ExtractionMethod.SPELLING, "string")
    manager.insert(string_entity, 1)
    assert (len(manager.retrieve(EmailEntity))) == 1

    email_entity = EmailEntity(
        0.74, ExtractionMethod.SPELLING, "einstein@salesforce.com"
    )
    manager.insert(email_entity, 0)
    print(manager.retrieve(EmailEntity))
