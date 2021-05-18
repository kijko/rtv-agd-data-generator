import sqlite3
import datetime

from matrix import MatrixEventHandler


class Database:
    def __init__(self, products):
        # init schema, add products to db, etc
        self._connection = None
        self._cursor = None
        try:
            self._connection = sqlite3.connect("../dev-data/" + _prepare_db_name())
            sqlite_create_table_query = "CREATE TABLE example (id INTEGER PRIMARY KEY);"

            self._cursor = self._connection.cursor()
            self._cursor.execute(sqlite_create_table_query)

            self._connection.commit()

        except sqlite3.Error as error:
            print("Error while creating a sqlite table", error)
            if self._connection is not None:
                self._connection.close()
                print("sqlite connection is closed")

            if self._cursor is not None:
                self._cursor.close()
                print("cursor is closed")

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
        print("** Zdarzenie ** - Utworzono nową osobę - " + repr(person))

