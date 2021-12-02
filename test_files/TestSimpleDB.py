# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import unittest
from Converse.simple_db.simple_db import SimpleDB


class TestSimpleDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sdb = SimpleDB()
        cls.sdb.set_db("test_files/db.yaml")

    def setUp(self):
        self.new_db = TestSimpleDB.sdb

    def test_get_order_status(self):
        res = self.new_db.get_order_status(1)
        self.assertEqual(res, "placed but not yet shipped")
        res = self.new_db.get_order_status(1000)
        self.assertEqual(res, "ERROR")

    def test_query_order(self):
        res = self.new_db.query_order(1)
        expected_qs = (
            "delivery_address:121 street Forest Hills||"
            + "product:pizza||quantity:10||"
            + "order_status:placed but not yet shipped"
        )
        self.assertEqual(res, expected_qs)
        res = self.new_db.query_order(1000)
        self.assertEqual(res, "None")

    def test_add_more_to_order(self):
        res = self.new_db.add_more_to_order(2, 1)
        self.assertEqual(res, "21")

    def test_single_step_verify(self):
        entities1 = {"email_address": "peter@hotmail.com"}
        entities2 = {"email_address": "peter@hotmail.com", "zip_code": "94301"}
        entities3 = {"email_address": "peter@hotmail.com", "zip_code": "93301"}

        res = self.new_db.single_step_verify(entities1)
        self.assertTrue(res)
        res = self.new_db.single_step_verify(entities2)
        self.assertTrue(res)
        res = self.new_db.single_step_verify(entities3)
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
