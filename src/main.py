from matrix import *
import products
import gui
import dbgen


def generate_big_data():
    available_products = [
        products.Product(1, "FRIDGE-1", 4999.99, "FRIDGE"),
        products.Product(2, "FRIDGE-2", 2499.89, "FRIDGE"),
        products.Product(3, "TV-1", 699.89, "TV"),
        products.Product(4, "TV-2", 6129.00, "TV"),
        products.Product(5, "TV-3", 8192.99, "TV")
    ]

    events = [Event(10, 4, 15, 4, 2021, 10, 2), Event(5, 5, 5, 5, 2021, 4, 5)]

    global_settings = GlobalSettings(1, 6, 2021, 10, events)

    poor_guys_needs = [Need("FRIDGE", 1, 1, 0.6), Need("TV", 2, 0, 0.4), Need("GAME_CONSOLE", 3, 2, 0.2)]
    poor_guys_profile = Profile("POOR", 18, 1000, 2000, poor_guys_needs, 0.05)

    middle_class_profile = Profile("MIDDLE_CLASS", 61, 3000, 5000, [Need("GAME_CONSOLE", 2, 1, 0.4)], 0.04)
    rich_man_profile = Profile("RICH_MEN", 21, 10000, 15000, [Need("GAME_CONSOLE", 1, 1, 0.4)], 0.03)

    profiles = [poor_guys_profile, middle_class_profile, rich_man_profile]

    db = dbgen.Database(available_products)
    in_mem_product_repository = products.ProductRepository(available_products)

    example_simulation = Matrix(
        Configuration(global_settings, profiles, in_mem_product_repository),
        db.get_collector()
    )

    example_simulation.run()

    db.end()


gui.run_gui(lambda: generate_big_data())


# generate_big_data()
