# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest

from Converse.entity.entity import (
    Entity,
    StringEntity,
    PersonEntity,
    LocationEntity,
    ZipCodeEntity,
    ExtractionMethod,
)


class TestEntity(unittest.TestCase):
    def setUp(self):
        self.entity1 = StringEntity(0.95, ExtractionMethod.NER, "some string")
        self.entity2 = StringEntity(0.95, ExtractionMethod.NER, "some string")
        self.entity3 = StringEntity(0.95, ExtractionMethod.SPELLING, "some string")
        self.entity4 = PersonEntity(0.95, ExtractionMethod.SPELLING, "some string")
        self.entity5 = StringEntity(1, ExtractionMethod.NER, "94301")
        self.entity6 = ZipCodeEntity(1, ExtractionMethod.NER, "94301")

    def test_equality_with_same_attributes(self):
        self.assertEqual(self.entity1, self.entity2)

    def test_inequality_with_different_attributes(self):
        self.assertNotEqual(self.entity1, self.entity3)

    def test_inequality_with_different_classes1(self):
        self.assertNotEqual(self.entity3, self.entity4)

    def test_inequality_with_different_classes2(self):
        self.assertNotEqual(self.entity5, self.entity6)

    def test_unique(self):
        entities = [
            self.entity1,
            self.entity2,
            self.entity3,
            self.entity4,
            self.entity5,
            self.entity6,
        ]
        unique_entities = Entity.unique(entities)
        self.assertEqual(unique_entities, [self.entity1, self.entity5])

    def test_unique_with_different_values_but_same_user_utt_value(self):
        """Tests that the unique function removes entities with different values
        but the same user utterance value based on the confidence score."""
        entities = [
            ZipCodeEntity(0.8, ExtractionMethod.NER, "94301", "94301", span={"end": 5}),
            LocationEntity(
                0.7,
                ExtractionMethod.NER,
                "94301",
                (("ZipCode", "94301"),),
                span={"end": 5},
            ),
        ]
        unique_entities = Entity.unique(entities)
        self.assertEqual(
            unique_entities,
            [entities[0]],
        )

    def test_unique_with_different_values_but_same_user_utt_value_order_swap(self):
        """Tests that the unique function removes entities with different values
        but the same user utterance value based on the confidence score. We expect
        that the highest score entity is kept even if the lower confidence entity
        occurs first in the list."""
        entities = [
            LocationEntity(
                0.7,
                ExtractionMethod.NER,
                "94301",
                (("ZipCode", "94301"),),
                span={"end": 5},
            ),
            ZipCodeEntity(0.8, ExtractionMethod.NER, "94301", "94301", span={"end": 5}),
        ]
        unique_entities = Entity.unique(entities)
        self.assertEqual(
            unique_entities,
            [entities[1]],
        )

    def test_unique_with_different_values_but_same_user_utt_value_different_span(self):
        """Tests that the unique function removes entities with different values
        but the same user utterance value and a different span based on the confidence
        score. We expect that only the highest scoring entity is kept even if the spans
        are different."""
        entities = [
            LocationEntity(
                0.7,
                ExtractionMethod.NER,
                "94301",
                (("ZipCode", "94301"),),
                span={"end": 5},
            ),
            ZipCodeEntity(
                0.8,
                ExtractionMethod.NER,
                "94301",
                "94301",
                span={"start": 5, "end": 10},
            ),
        ]
        unique_entities = Entity.unique(entities)
        self.assertEqual(
            unique_entities,
            [entities[1]],
        )

    def test_unique_by_value_wtih_all_unique_items(self):
        """This test tests `unique_by_value`. Since the entities have different values,
        the unique entities don't have any entities filtered out."""
        entities = [
            LocationEntity(
                0.7,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value=(("ZipCode", "94301"),),
                span={"end": 5},
            ),
            ZipCodeEntity(
                0.8,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value="94301",
                span={"start": 5, "end": 10},
            ),
        ]
        unique_entities = Entity.unique_by_value(entities)
        self.assertEqual(
            unique_entities,
            entities,
        )

    def test_unique_by_value_wtih_nonunique_items(self):
        """This test tests `unique_by_value`. Since the entities have the same value,
        the entity with the lower score is filtered out."""
        entities = [
            StringEntity(
                0.6,
                ExtractionMethod.NER,
                user_utt_value="94301",
                span={"start": 5, "end": 10},
            ),
            ZipCodeEntity(
                0.8,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value="94301",
                span={"start": 5, "end": 10},
            ),
        ]
        unique_entities = Entity.unique_by_value(entities)
        self.assertEqual(
            unique_entities,
            [entities[1]],
        )

    def test_unique_by_user_utt_value_wtih_unique_items(self):
        """This test tests `unique_by_user_utt_value`. Since the entities have different
        user utterance values, the unique entities don't have any entities filtered
        out."""
        entities = [
            ZipCodeEntity(
                0.6,
                ExtractionMethod.NER,
                user_utt_value="24307",
                normalized_value="24307",
                span={"start": 5, "end": 10},
            ),
            ZipCodeEntity(
                0.8,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value="94301",
                span={"start": 5, "end": 10},
            ),
        ]
        unique_entities = Entity.unique_by_user_utt_value(entities)
        self.assertEqual(
            unique_entities,
            entities,
        )

    def test_unique_by_user_utterance_value_with_nonunique_items(self):
        """This test tests `unique_by_user_utt_value`. Since the entities have the same
        user utterance values, the entity with a lower score is filtered out."""
        entities = [
            LocationEntity(
                0.7,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value=(("ZipCode", "94301"),),
                span={"end": 5},
            ),
            ZipCodeEntity(
                0.8,
                ExtractionMethod.NER,
                user_utt_value="94301",
                normalized_value="94301",
                span={"start": 5, "end": 10},
            ),
        ]
        unique_entities = Entity.unique_by_user_utt_value(entities)
        self.assertEqual(
            unique_entities,
            [entities[1]],
        )


if __name__ == "__main__":
    unittest.main()
