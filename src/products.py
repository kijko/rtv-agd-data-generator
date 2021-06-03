import csv


class CSVInMemoryProductRepository:
    def __init__(self, csv_file_path):
        print("Creating product repo from file: " + csv_file_path)
        self._products = []

        with open(csv_file_path, 'r') as csv_file:
            id = 1
            reader = csv.reader(csv_file)

            # omijamy nagłówek
            next(reader, None)

            for row in reader:
                print(row)
                self._products.append(Product(id, row[0], float(row[1]), row[2]))

            print("   Wczytano " + str(len(self._products)) + " produktów: ")
            for product in self._products:
                print("      " + repr(product))

            csv_file.close()

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

