import sqlite3
import datetime

from matrix import MatrixEventHandler


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
        return DbDataCollector()

    def end(self):
        self._cursor.close()
        self._connection.close()


def _prepare_db_name():
    datetime_stamp = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S-%f")

    return "generated_" + datetime_stamp + ".db"


class DbDataCollector(MatrixEventHandler):

    def person_was_born(self, person):
        print("************* Zdarzenie ************ - Utworzono nową osobę - " + repr(person))

    def went_to_shop(self, person, sim_datetime):
        print("************* Zdarzenie ************ - Osoba poszła do sklepu ! "
              + sim_datetime.strftime("%d-%m-%y") + " " + repr(person))

    def shopping(self, person, sim_datetime, bought_products):
        print("************* Zdarzenie ************ - ZAKUPKI ! "
              + sim_datetime.strftime("%d-%m-%y") + " " + person.id + " Paragon: " + str(bought_products))

    def person_died(self, person):
        print("************* Zdarzenie ************ - Koniec życia pełnego konsumpcji i pracy ! RIP " + repr(person))
