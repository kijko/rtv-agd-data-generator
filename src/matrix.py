import datetime
import calendar
import random

_day = datetime.timedelta(days=1)


class Matrix:

    def __init__(self, config):
        self.config = config
        self.groups = _create_groups(config.global_settings.population, config.profiles)

    def run(self):
        for group in self.groups:
            print("---- Group ----")
            print(group.name)
            print(group.population)
            print(group.salary_from)
            print(group.salary_to)
            print(group.generate_salary())
            print("---- ----- ----")

        Life(
            self.config.global_settings.start_month,
            self.config.global_settings.end_month,
            self.config.global_settings.year
        ).start()


def _create_groups(population, profiles):
    class Group:
        def __init__(self, name, population, salary_from, salary_to):
            self.salary_to = salary_to
            self.salary_from = salary_from
            self.population = population
            self.name = name

        def generate_salary(self):
            return random.randint(self.salary_from, self.salary_to)

    def calculate_group_population(percent_of_people):
        group_population_float = population * (percent_of_people / 100)
        group_population_int = int(group_population_float)

        if group_population_float - float(group_population_int) >= 0.5:
            return group_population_int + 1
        else:
            return group_population_int

    groups = []

    for profile in profiles:
        groups.append(
            Group(
                profile.name,
                calculate_group_population(profile.percent_of_people),
                profile.salary_from,
                profile.salary_to
            )
        )

    return groups


class Life:
    def __init__(self, start_month, end_month, year):
        self._start_date = datetime.date(year, start_month, 1)
        self._last_day_date = datetime.date(year, end_month, calendar.monthrange(year, end_month)[1])
        self._actual_date = self._start_date

    def start(self):
        while self._actual_date <= self._last_day_date:
            print(self._actual_date.strftime("Actual time: %d %m %y"))
            print("doing something...")
            self._actual_date += _day




class Configuration:
    def __init__(self, global_settings, profiles):
        self.global_settings = global_settings
        self.profiles = profiles


class GlobalSettings:
    def __init__(self, start_month, end_month, year, population):
        self.population = population
        self.year = year
        self.end_month = end_month
        self.start_month = start_month


class Profile:
    def __init__(self, name, percent_of_people, salary_from, salary_to):
        self.salary_to = salary_to
        self.salary_from = salary_from
        self.percent_of_people = percent_of_people
        self.name = name


def _createSlaveWithProfile(profile):
    # todo
    pass

