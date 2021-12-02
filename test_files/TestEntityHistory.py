# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest

from Converse.entity.entity_history import EntityHistoryManager
from Converse.entity.entity import (
    EmailEntity,
    StringEntity,
    ExtractionMethod,
    ZipCodeEntity,
    CardinalEntity,
)


class EntityHistoryTest(unittest.TestCase):
    def setUp(self):
        self.manager = EntityHistoryManager()
        self.email_entity1 = EmailEntity(
            0.9, ExtractionMethod.SPELLING, "peter@hotmail.com"
        )
        self.email_entity2 = EmailEntity(0.5, ExtractionMethod.NER, "peter@hotmail.com")
        self.email_entity3 = EmailEntity(0.5, ExtractionMethod.NER, "peter@hotmail.com")
        self.diff_email_entity = EmailEntity(
            0.74, ExtractionMethod.SPELLING, "einstein@salesforce.com"
        )
        self.string_entity = StringEntity(
            1, ExtractionMethod.SPELLING, "peter@hotmail.com"
        )

    def test_insert_identical_entities(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity1, turn=1)
        self.assertEqual(len(self.manager.history[1]), 1)

    def test_insert_equivalent_entities(self):
        self.manager.insert(self.email_entity2, turn=1)
        self.manager.insert(self.email_entity3, turn=1)
        self.assertEqual(len(self.manager.history[1]), 1)

    def test_insert_different_entities(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity2, turn=1)
        self.assertEqual(len(self.manager.history[1]), 2)

    def test_retrieve_by_score(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity2, turn=1)
        self.manager.insert(self.diff_email_entity, turn=1)
        self.assertEqual(
            self.manager.retrieve(EmailEntity, turns=[1]),
            [self.email_entity1, self.diff_email_entity],
        )

    def test_retrieve_by_class1(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity2, turn=1)
        self.manager.insert(self.string_entity, turn=1)
        self.assertEqual(self.manager.retrieve(StringEntity), [self.string_entity])

    def test_retrieve_by_class2(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity2, turn=1)
        self.manager.insert(self.string_entity, turn=1)
        self.assertEqual(self.manager.retrieve(EmailEntity), [self.email_entity1])

    def test_retrieve_from_correct_turn(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.manager.insert(self.email_entity2, turn=2)
        self.manager.insert(self.diff_email_entity, turn=3)
        self.assertEqual(
            self.manager.retrieve(EmailEntity, turns=[1]), [self.email_entity1]
        )
        self.assertEqual(
            self.manager.retrieve(EmailEntity, turns=[1, 2]), [self.email_entity1]
        )
        self.assertEqual(
            self.manager.retrieve(EmailEntity, turns=[2, 3]),
            [self.diff_email_entity, self.email_entity2],
        )
        self.assertEqual(
            self.manager.retrieve(EmailEntity),
            [self.email_entity1, self.diff_email_entity],
        )

    def test_retrieve_from_incorrect_turn(self):
        self.manager.insert(self.email_entity1, turn=1)
        self.assertEqual(self.manager.retrieve(EmailEntity, turns=[2]), [])

    def test_retrieve_with_entity_name(self):
        self.manager.insert_named_entity("work_email", self.email_entity1)
        self.manager.insert_named_entity("personal_email", self.email_entity2)
        self.manager.insert(self.email_entity1, 1)
        self.manager.insert(self.string_entity, 2)
        self.assertEqual(
            self.manager.retrieve(EmailEntity, entity_name="personal_email"),
            [self.email_entity2],
        )
        self.assertEqual(
            self.manager.retrieve(EmailEntity, entity_name="email"),
            [self.email_entity1],
        )

    def test_remove_entity(self):
        self.manager.insert(self.email_entity1, 1)
        # remove a different email; should have no effect
        self.manager.remove(self.diff_email_entity)
        self.assertEqual(self.manager.history[1], {self.email_entity1})

        # remove the correct entity, but with a different score; should remove it
        self.manager.remove(self.email_entity2)
        self.assertEqual(self.manager.history[1], set())

    def test_remove_named_entity(self):
        self.manager.insert_named_entity("work_email", self.email_entity1)
        self.manager.insert_named_entity("personal_email", self.email_entity2)

        # remove a named entity
        self.manager.remove_named_entity("work_email")
        self.assertEqual(self.manager.retrieve(EmailEntity, None, "work_email"), [])
        self.assertEqual(
            self.manager.retrieve(EmailEntity, None, "personal_email"),
            [self.email_entity2],
        )

    def test_remove_same_value_different_type(self):
        """
        We want to test the case when entities of different types were created from
        the same user utterance. Even if they are of different type, `remove` call
        should delete all of them, regardless of the provided type
        """
        zip_code_entity = ZipCodeEntity(
            score=1.0, method=ExtractionMethod.NER, user_utt_value="94301"
        )
        cardinal_entity = CardinalEntity(
            score=0.5, method=ExtractionMethod.NER, user_utt_value=94301
        )

        # remove cardinal to see if the zip code is also removed
        self.manager.insert(zip_code_entity, 1)
        self.manager.insert(cardinal_entity, 1)
        self.manager.remove(cardinal_entity)
        self.assertEqual(self.manager.history[1], set())

        # repeat with removing zip code to see if cardinal is also removed
        self.manager.insert(zip_code_entity, 1)
        self.manager.insert(cardinal_entity, 1)
        self.manager.remove(zip_code_entity)
        self.assertEqual(self.manager.history[1], set())


if __name__ == "__main__":
    unittest.main()
