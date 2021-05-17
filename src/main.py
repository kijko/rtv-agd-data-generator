from matrix import *
import products
import gui

example_simulation = Matrix(
    Configuration(
        GlobalSettings(
            1,
            6,
            2021,
            10,
            0.05,
            [
                Event(10, 4, 15, 4, 2021, 10, 2),
                Event(5, 5, 5, 5, 2021, 4, 5)
            ]
        ),
        [
            Profile(
                "POOR",
                18,
                1000,
                2000,
                [
                    Need("FRIDGE", 1, 1, 0.6),
                    Need("TV", 2, 0, 0.4),
                    Need("GAME_CONSOLE", 3, 2, 0.2)
                ]
            ),
            Profile(
                "MIDDLE_CLASS",
                61,
                3000,
                5000,
                [
                    Need("GAME_CONSOLE", 2, 1, 0.4)
                ]
            ),
            Profile(
                "RICH_MEN",
                21,
                10000,
                15000,
                [
                    Need("GAME_CONSOLE", 1, 1, 0.4)
                ]
            )
        ],
        products.ProductRepository([
            products.Product("FRIDGE-1", 4999.99, "FRIDGE"),
            products.Product("FRIDGE-2", 2499.89, "FRIDGE"),
            products.Product("TV-1", 699.89, "TV"),
            products.Product("TV-2", 6129.00, "TV"),
            products.Product("TV-3", 8192.99, "TV")
        ])
    )
)

gui.run_gui(lambda: example_simulation.run())
