
class ProductRepository:
    def __init__(self, products):
        self._products = products

    def find_by_category_and_max_price(self, category, max_price):
        list_copy = self._products.copy()
        return list(filter(lambda product: product.category == category and product.price <= max_price, list_copy))


class Product:
    def __init__(self, identity, name, price, category):
        self.id = identity
        self.category = category
        self.price = price
        self.name = name

    def __repr__(self):
        return "Product: [" + str(self.id) + ", " + self.category + ", " + self.name + ", " + str(self.price) + "]"

