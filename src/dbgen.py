import sqlite3
import datetime
import uuid
import hashlib
import random
import string

from matrix import MatrixEventHandler
from faker import Faker

fake = Faker()


# noinspection SqlNoDataSourceInspection
class Database:
    def __init__(self, products):
        self._connection = None
        self._cursor = None
        try:

            self._connection = sqlite3.connect("../dev-data/" + _prepare_db_name())
            self._cursor = self._connection.cursor()

            self._init_db(products)

        except sqlite3.Error as error:
            print("Error while creating a sqlite table", error)
            if self._connection is not None:
                self._connection.close()
                print("sqlite connection is closed")

            if self._cursor is not None:
                self._cursor.close()
                print("cursor is closed")

    def _init_db(self, products):
        fd = open("./schema.sql", "r")
        schema_sql = fd.read()
        fd.close()

        schema_commands = schema_sql.split(";")

        for command in schema_commands:
            self._cursor.execute(command)

        insert_product = """INSERT INTO product(id, name, price, category) VALUES(?, ?, ?, ?)"""

        for product in products:
            self._cursor.execute(insert_product, (product.id, product.name, product.price, product.category))

        self._connection.commit()

    def get_collector(self):
        return DbDataCollector(self._connection, self._cursor)

    def end(self):
        self._connection.commit()
        self._cursor.close()
        self._connection.close()


def _prepare_db_name():
    datetime_stamp = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S-%f")

    return "generated_" + datetime_stamp + ".db"


def generate_fake_password_hash():
    pw = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    hash = hashlib.md5(pw.encode())

    return hash.hexdigest()

def generate_fake_payment_method():
    one_two_or_three = random.randint(1, 3)

    if one_two_or_three == 1:
        return "CASH"
    elif one_two_or_three == 2:
        return "CARD"
    else:
        return "CREDIT"


class DbDataCollector(MatrixEventHandler):

    def __init__(self, connection, cursor):
        self._connection = connection
        self._cursor = cursor
        self._count_person = 0

    def person_was_born(self, person):
        self._count_person += 1
        # print("************* Zdarzenie ************ - Utworzono nową osobę - " + repr(person))

        insert_customer_sql = """INSERT INTO customer(id, first_name, last_name, email, password_hash, phone_number, created_at, group_name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"""

        self._cursor.execute(insert_customer_sql, (person.id,
                                                   fake.first_name(),
                                                   fake.last_name(),
                                                   fake.ascii_safe_email(),
                                                   generate_fake_password_hash(),
                                                   fake.phone_number(),
                                                   fake.date_time(),
                                                   person.group_name))

        insert_address_sql = """ INSERT INTO address(customer_id, country, city, street, apartment) VALUES(?, ?, ?, ?, ?) """

        self._cursor.execute(insert_address_sql, (person.id,
                                                  fake.country(),
                                                  fake.city(),
                                                  fake.street_name(),
                                                  fake.building_number()))


    def went_to_shop(self, person, sim_datetime, visit_id):
        # print("************* Zdarzenie ************ - Osoba poszła do sklepu ! "
        #       + sim_datetime.strftime("%d-%m-%y") + " " + repr(person))

        insert_visit_sql = """ INSERT INTO visit(id, customer_id, visit_at) VALUES(?, ?, ?)"""

        self._cursor.execute(insert_visit_sql, (visit_id, person.id, sim_datetime))

    def shopping(self, person, sim_datetime, bought_products, visit_id):
        # print("************* Zdarzenie ************ - ZAKUPKI ! "
        #       + sim_datetime.strftime("%d-%m-%y") + " " + person.id + " Paragon: " + str(bought_products))

        if len(bought_products) > 0:
            insert_order_sql = """ INSERT INTO customer_order(id, created_at, payment_type, visit_id) VALUES(?, ?, ?, ?)"""

            order_id = str(uuid.uuid4())
            self._cursor.execute(insert_order_sql, (order_id, sim_datetime, generate_fake_payment_method(), visit_id))

            insert_product_to_order_sql = """ INSERT INTO ordered_product(product_id, order_id) VALUES(?, ?)"""

            for product in bought_products:
                self._cursor.execute(insert_product_to_order_sql, (product.id, order_id))

    def person_died(self, person):
        if self._count_person % 1_000 == 0:
            self._connection.commit()
        # print("************* Zdarzenie ************ - Koniec życia pełnego konsumpcji i pracy ! RIP " + repr(person))
        # self._connection.commit()
