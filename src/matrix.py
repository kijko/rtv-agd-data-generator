import datetime
import calendar
import random

_day = datetime.timedelta(days=1)


class Matrix:

    def __init__(self, config):
        self.config = config
        self.groups = _create_groups(config.global_settings.population, config.profiles)

    def run(self):
        world = World(
            self.config.global_settings.start_month,
            self.config.global_settings.end_month,
            self.config.global_settings.year,
            self.config.global_settings.daily_go_to_shop_probability,
            self.config.global_settings.events
        )
        for group in self.groups:
            print("Run matrix simulation for group: " + group.name)
            while group.has_next_slave():
                slave = group.next_slave()
                world.start(slave)
                world.reset()


class Group:
    def __init__(self, name, population, salary_from, salary_to):
        self._salary_to = salary_to
        self._salary_from = salary_from
        self._max_population = population
        self._actual_population = 0
        self.name = name

    def has_next_slave(self):
        return self._actual_population < self._max_population

    def next_slave(self):
        if self.has_next_slave():
            self._actual_population += 1
            slave = Slave(self._actual_population, self.name, random.randint(self._salary_from, self._salary_to))

            return slave
        else:
            return None


class Slave:
    def __init__(self, number_in_group, group_name, salary):
        self.id = group_name + "-" + str(number_in_group)

        self._salary = salary
        self.account_balance = 0.0

    def pay_the_paycheck(self):
        self.account_balance += self._salary


def _create_groups(population, profiles):
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


class World:
    def __init__(self, start_month, end_month, year, regular_go_to_shop_probability, events):
        self._regular_go_to_shop_probability = regular_go_to_shop_probability
        self._start_date = datetime.date(year, start_month, 1)
        self._last_day_date = datetime.date(year, end_month, calendar.monthrange(year, end_month)[1])
        self._actual_date = self._start_date
        self._events = events

    def start(self, slave):
        if self._actual_date == self._last_day_date:
            print("The world is over. Press reset button")
        else:
            print("Slave with id: " + slave.id + " has been placed in the world.")
            while self._actual_date <= self._last_day_date:
                actual_date_str = self._actual_date.strftime("%d-%m-%y")
                print("  Day " + actual_date_str + " begins.")

                if self._actual_date.day == 1:
                    slave.pay_the_paycheck()
                    print("    [Payday ! Actual slaves account: " + str(slave.account_balance) + "]")

                if self._will_go_to_shop():
                    print("    Slave goes to the shop !")
                else:
                    print("    Slave does nothing...")

                self._actual_date += _day
            print("End of the world for slave with id: " + slave.id)

    def reset(self):
        print("World reset occurs")
        self._actual_date = self._start_date

    def _will_go_to_shop(self):
        event = self._get_actual_event()

        if event is None:
            return random.random() <= self._regular_go_to_shop_probability
        else:
            print("    [probability bonus !]")
            return random.random() <= event.go_to_shop_probability

    def _get_actual_event(self):
        for event in self._events:
            if event.is_event_date(self._actual_date):
                return event

        return None





class Configuration:
    def __init__(self, global_settings, profiles):
        self.global_settings = global_settings
        self.profiles = profiles


class GlobalSettings:
    def __init__(self, start_month, end_month, year, population, daily_go_to_shop_probability, events):
        self.events = events
        self.daily_go_to_shop_probability = daily_go_to_shop_probability
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


class Event:
    def __init__(self, day_from, month_from, day_to, month_to, year, go_to_shop_probability):
        self.go_to_shop_probability = go_to_shop_probability
        self._first_day = datetime.date(year, month_from, day_from)
        self._last_day = datetime.date(year, month_to, day_to)

    def is_event_date(self, date):
        return self._first_day <= date <= self._last_day

