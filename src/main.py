from matrix import *
import gui
import dbgen
# todo main-prod/main-dev


def generate_big_data(progress_handler, simulation_config):
    db = dbgen.Database(simulation_config.product_repository.find_all())

    print(repr(simulation_config))

    simulation = Matrix(
        simulation_config,
        db.get_collector(),
        progress_handler
    )

    simulation.run()

    db.end()


gui.run_gui(generate_big_data)


# generate_big_data()
