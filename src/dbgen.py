import sqlite3

from matrix import MatrixEventHandler


class Database:
    def __init__(self, products):
        # init schema, add products to db, etc
        self._connection = None
        self._cursor = None
        try:
            self._connection = sqlite3.connect('../dev-data/SQLite_Python.db')
            sqlite_create_table_query = "CREATE TABLE example (id INTEGER PRIMARY KEY);"

            self._cursor = self._connection.cursor()
            self._cursor.execute(sqlite_create_table_query)

            self._connection.commit()

            self._cursor.close()

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


class DbDataCollector(MatrixEventHandler):

    def person_was_born(self, person):
        print("** Zdarzenie ** - Utworzono nową osobę - " + repr(person))

