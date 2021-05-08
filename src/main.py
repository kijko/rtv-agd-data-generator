from matrix import *

Matrix(
    Configuration(
        GlobalSettings(
            1,
            6,
            2021,
            10,
            0.05,
            [
                Event(10, 4, 15, 4, 2021, 0.5),
                Event(5, 5, 5, 5, 2021, 0.2)
            ]
        ),
        [
            Profile("POOR", 18, 1000, 2000),
            Profile("MIDDLE_CLASS", 61, 3000, 5000),
            Profile("RICH_MEN", 21, 10000, 15000)
        ]
    )
).run()


