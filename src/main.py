from matrix import *
import products
import gui
import dbgen
# todo main-prod/main-dev


def generate_big_data(progress_handler, simulator_input):
    in_mem_product_repository = products.CSVInMemoryProductRepository(simulator_input.csv_input_file_path)
    db = dbgen.Database(in_mem_product_repository.find_all())

    config = YMLConfiguration(simulator_input.yml_input_file_path, in_mem_product_repository)

    example_simulation = Matrix(
        config,
        db.get_collector(),
        progress_handler
    )

    example_simulation.run()

    db.end()


gui.run_gui(generate_big_data)


# generate_big_data()
