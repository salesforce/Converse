# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause

import os

from Converse.simple_db.database import db, User, Order
from pony.orm import db_session, commit
from Converse.utils.yaml_parser import load_yaml


class SimpleDB:
    def __init__(
        self,
        db_file=os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "database.sqlite"
        ),
        overwrite=True,
    ):
        if overwrite and os.path.exists(db_file):
            os.remove(db_file)

        db.bind(provider="sqlite", filename=db_file, create_db=overwrite)
        db.generate_mapping(create_tables=overwrite)

    @db_session
    def set_db(self, db_data_file_path):
        dat = load_yaml(db_data_file_path)
        for item in dat["user"]:
            User(**item)

        for item in dat["order"]:
            u = User[item["uid"]]
            del item["uid"]
            Order(**item, user=u)
        commit()

    @db_session
    def _verify_user(self, entities, cur_entity=None):
        arr = []
        for k, v in entities.items():
            if cur_entity and k != cur_entity:
                continue
            if getattr(User, k):
                if v == "WRONG INFO!":
                    continue
                arr.append(f" {k} = '{v}' ")
        sql = "select * from User where " + " and ".join(arr)
        users = User.select_by_sql(sql)
        return users

    def single_step_verify(
        self,
        entities,
        cur_entity=None,
    ):
        # type: (...) -> bool
        """
        single step verification using single or multiple entities
        """
        users = self._verify_user(entities, cur_entity)
        return len(users) == 1

    @db_session
    def add_more_to_order(self, oid: int, value: int):
        order = Order.get(oid=oid)
        if not order:
            return "ERROR"
        new_value = order.quantity + value
        order.quantity = new_value
        commit()
        return f"{new_value}"

    @db_session
    def query_order(self, oid: int):
        order = Order.get(oid=oid)
        if not order:
            return "None"
        arr = []
        arr.append(f"delivery_address:{order.delivery_address}")
        arr.append(f"product:{order.product}")
        arr.append(f"quantity:{order.quantity}")
        arr.append(f"order_status:{order.order_status}")
        return "||".join(arr)

    @db_session
    def get_order_status(self, oid: int):
        order = Order.get(oid=oid)
        if not order:
            return "ERROR"
        else:
            return order.order_status

    @db_session
    def test_db(self):
        # res = db.select("zip_code from User where email_address = 'peter@hotmail.com'")
        res = db.select(" zip_code from User where uid = 1 ")
        return res


if __name__ == "__main__":
    simple_db = SimpleDB()
    simple_db.set_db("./test_files/db.yaml")
    entities = {"email_address": "peter@hotmail.com"}
    ans = simple_db.single_step_verify(entities, cur_entity="email_address")
    print(f"ans is: {ans}")
