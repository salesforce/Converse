from pony.orm import Database, PrimaryKey, Required, Set

db = Database()


class User(db.Entity):
    uid = PrimaryKey(int)
    name = Required(str)
    phone_number = Required(str)
    email_address = Required(str)
    zip_code = Required(str)
    address = Required(str)
    orders = Set("Order")


class Order(db.Entity):
    user = Required(User)
    oid = PrimaryKey(int)
    delivery_address = Required(str)
    product = Required(str)
    quantity = Required(int)
    order_status = Required(str)
