from matrix import *
import products
import gui
import dbgen
# todo main-prod/main-dev


def generate_big_data(progress_handler):
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

    global_settings = GlobalSettings(1, 2020, 6, 2021, 10_040, date_bonuses, needs_associations)

    poor_guys_needs = [Need("FRIDGE", 1, 1, 0.6), Need("TV", 2, 0, 0.4), Need("GAME_CONSOLE", 3, 2, 0.2), Need("PHONE", 2, 3, 0.6)]
    poor_guys_profile = Profile("POOR", 18, 1000, 1000, 2000, poor_guys_needs, 0.05)

    middle_class_profile = Profile("MIDDLE_CLASS", 61, 2000, 3000, 5000, [Need("GAME_CONSOLE", 2, 1, 0.4)], 0.04)
    rich_man_profile = Profile("RICH_MEN", 21, 3000, 10000, 15000, [Need("GAME_CONSOLE", 1, 1, 0.4)], 0.03)

    profiles = [poor_guys_profile, middle_class_profile, rich_man_profile]

    in_mem_product_repository = products.CSVInMemoryProductRepository("csv-file-path-here!")
    db = dbgen.Database(in_mem_product_repository.find_all())

    example_simulation = Matrix(
        Configuration(global_settings, profiles, in_mem_product_repository),
        db.get_collector(),
        progress_handler
    )

    example_simulation.run()

    db.end()


gui.run_gui(generate_big_data)


# generate_big_data()
