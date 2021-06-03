
class CSVInMemoryProductRepository:
    def __init__(self, csv_file_path):
        print("Creating product repo from file: " + csv_file_path)
        self._products = [
            Product(1, "FRIDGE-1", 4999.99, "FRIDGE"),
            Product(2, "FRIDGE-2", 2499.89, "FRIDGE"),
            Product(3, "TV-1", 699.89, "TV"),
            Product(4, "TV-2", 6129.00, "TV"),
            Product(5, "TV-3", 8192.99, "TV"),
            Product(6, "X-ONE GAMEPAD", 299.00, "WIRELESS-GAMEPAD"),
            Product(7, "Duracell AAA", 19.99, "AAA-BATTERIES"),
            Product(8, "Coffee maker 2000", 3999.99, "COFFEE-MACHINE"),
            Product(9, "Lavazza 500g", 24.89, "COFFEE"),
            Product(10, "iPhone 15S", 799.99, "PHONE"),
            Product(11, "iPhone special phone charger", 299.00, "PHONE-CHARGER"),
            Product(12, "iPhone USB Cable", 89.00, "PHONE-CABLE"),
            Product(13, "Netflix subscribtion", 39.99, "STREAMING-SERVICE-SUB"),
            Product(14, "Whirpool super washer", 599.90, "WASHING_MACHINE")
        ]

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

