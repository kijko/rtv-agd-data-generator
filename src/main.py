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
        products.Product(5, "TV-3", 8192.99, "TV"),
        products.Product(6, "X-ONE GAMEPAD", 299.00, "WIRELESS-GAMEPAD"),
        products.Product(7, "Duracell AAA", 19.99, "AAA-BATTERIES"),
        products.Product(8, "Coffee maker 2000", 3999.99, "COFFEE-MACHINE"),
        products.Product(9, "Lavazza 500g", 24.89, "COFFEE"),
        products.Product(10, "iPhone 15S", 799.99, "PHONE"),
        products.Product(11, "iPhone special phone charger", 299.00, "PHONE-CHARGER"),
        products.Product(12, "iPhone USB Cable", 89.00, "PHONE-CABLE"),
        products.Product(13, "Netflix subscribtion", 39.99, "STREAMING-SERVICE-SUB"),
        products.Product(14, "Whirpool super washer", 599.90, "WASHING_MACHINE")
    ]

    date_bonuses = [DateProbabilityBonus(10, 4, 15, 4, 2021, 10, 2), DateProbabilityBonus(5, 5, 5, 5, 2021, 4, 5)]

    needs_associations = [
        StrongAssociation("WIRELESS-GAMEPAD", "AAA-BATTERIES", one_to_one, 0.8),
        StrongAssociation("COFFEE-MACHINE", "COFFEE", one_to_many, 0.5),
        StrongAssociation("PHONE", "PHONE-CHARGER", one_to_one, 0.4),
        StrongAssociation("PHONE-CHARGER", "PHONE-CABLE", one_to_one, 0.3),
        Association("TV", "STREAMING-SERVICE-SUB", one_to_many, 0.9),
        LooselyCoupledAssociation("FRIDGE", "WASHING_MACHINE", 0.8, 0.6),
        LooselyCoupledAssociation("TV", "FRIDGE", 0.8, 0.6),
        LooselyCoupledAssociation("PHONE", "TV", 0.8, 0.6)
    ]

    global_settings = GlobalSettings(1, 6, 2021, 10, date_bonuses, needs_associations)

    poor_guys_needs = [Need("FRIDGE", 1, 1, 0.6), Need("TV", 2, 0, 0.4), Need("GAME_CONSOLE", 3, 2, 0.2), Need("PHONE", 2, 3, 0.6)]
    poor_guys_profile = Profile("POOR", 18, 1000, 1000, 2000, poor_guys_needs, 0.05)

    middle_class_profile = Profile("MIDDLE_CLASS", 61, 2000, 3000, 5000, [Need("GAME_CONSOLE", 2, 1, 0.4)], 0.04)
    rich_man_profile = Profile("RICH_MEN", 21, 3000, 10000, 15000, [Need("GAME_CONSOLE", 1, 1, 0.4)], 0.03)

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
