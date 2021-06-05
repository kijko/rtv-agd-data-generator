import csv
from error import ValidationError


class CSVInMemoryProductRepository:
    def __init__(self, csv_file_path):
        print("Creating product repo from file: " + csv_file_path)

        try:
            self._products = []

            with open(csv_file_path, "r", encoding='utf-8') as csv_file:
                id = 1
                reader = csv.reader(csv_file, delimiter=";")

                # omijamy nagłówek
                next(reader, None)

                for row in reader:
                    if len(row[0]) > 0 and len(row[1]) > 0 and len(row[2]) > 0:
                        self._products.append(Product(id, row[0], float(row[1].replace(",", ".")), row[2]))
                        id += 1

                print("   Wczytano " + str(len(self._products)) + " produktów: ")
                for product in self._products:
                    print("      " + repr(product))

                csv_file.close()
        except Exception as e:
            raise ValidationError(repr(e))

    def find_by_category_and_max_price(self, category, max_price):
        list_copy = self._products.copy()
        return list(filter(lambda product: product.category == category and product.price <= max_price, list_copy))

    def find_all(self):
        return self._products


class Product:
    def __init__(self, identity, name, price, category):
        self.id = identity
        self.category = category
        self.price = price
        self.name = name

    def __repr__(self):
        return "[" + str(self.id) + ", " + self.category + ", " + self.name + ", " + str(self.price) + "]"

