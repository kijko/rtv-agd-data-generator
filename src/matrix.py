import datetime
import calendar
import random
import queue

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
            self.config.global_settings.events,
            self.config.product_repository
        )
        for group in self.groups:

            print("Uruchomiono symulacje dla grupy: " + group.name)
            while group.has_next_slave():
                slave = group.next_slave()
                world.start(slave)
                world.reset()


class Group:
    def __init__(self, name, population, salary_from, salary_to, needs):
        self._salary_to = salary_to
        self._salary_from = salary_from
        self._max_population = population
        self._actual_population = 0
        self.needs = needs
        self.name = name

    def has_next_slave(self):
        return self._actual_population < self._max_population

    def next_slave(self):
        if self.has_next_slave():
            self._actual_population += 1
            slave = Slave(self._actual_population, self.name, random.randint(self._salary_from, self._salary_to), self.needs)

            return slave
        else:
            return None


class Slave:
    def __init__(self, number_in_group, group_name, salary, needs):
        self.id = group_name + "-" + str(number_in_group)

        self._salary = salary
        self.needs = needs

        self.account_balance = 0.0

    def pay_the_paycheck(self):
        self.account_balance += self._salary

    def prepare_shopping_list(self):
        q = queue.Queue()

        copied_needs = self.needs.copy()
        copied_needs.sort(key=lambda item: item.priority)

        for need in copied_needs:
            for i in range(need.num_of_items):
                q.put(need.category)

        return q

    def buy_or_not_to_buy(self, product):
        need_of_product = list(filter(lambda need: need.category == product.category, self.needs.copy()))[0]

        if random.random() <= need_of_product.indecision_factor:
            return "NOT_TO_BUY"
        else:
            self._satisfy_need(product, need_of_product)

            return "BUY"

    def _satisfy_need(self, product, need_of_product):
        self.account_balance -= product.price

        if need_of_product.num_of_items > 1:
            need_of_product.num_of_items -= 1
        else:
            self.needs = list(filter(lambda need: need.category != need_of_product.category, self.needs.copy()))

    def __repr__(self):
        needs_str = "["

        for need in self.needs:
            needs_str += repr(need) + ", "

        needs_str += "]"


        return "Osoba: [id=" + self.id + ", salary=" + str(self._salary) + ", needs=" + needs_str + ", acc_balance=" + str(self.account_balance) + "]"


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
                profile.salary_to,
                profile.needs
            )
        )

    return groups


class World:
    def __init__(self, start_month, end_month, year, regular_go_to_shop_probability, events, product_repository):
        self._regular_go_to_shop_probability = regular_go_to_shop_probability
        self._start_date = datetime.date(year, start_month, 1)
        self._last_day_date = datetime.date(year, end_month, calendar.monthrange(year, end_month)[1])
        self._actual_date = self._start_date
        self._events = events
        self._product_repository = product_repository

    def start(self, slave):
        if self._actual_date == self._last_day_date:
            print("Świat się zakończył. Zresetuj go")
        else:
            needStr = ""
            for need in slave.needs:
                needStr += "[" + need.category + ", " + str(need.num_of_items) + ", " + str(need.priority) + ", " + str(need.indecision_factor) + "] "

            print("Osoba z id: " + slave.id + " i potrzebami: " + needStr + "została umieszona w symulacji.")

            while self._actual_date <= self._last_day_date:
                actual_date_str = self._actual_date.strftime("%d-%m-%y")
                print("  Dzień " + actual_date_str + " zaczął się.")

                if self._actual_date.day == 1:
                    slave.pay_the_paycheck()
                    print("    [Wypłata ! Aktualna kwota jaką posiada osoba: " + str(slave.account_balance) + "]")

                if self._will_go_to_shop():
                    print("    Osoba poszła do sklepu !")
                    print("    Stan osoby: " + repr(slave))
                    shopping_list = slave.prepare_shopping_list()

                    while not shopping_list.empty():
                        product_category = shopping_list.get()
                        print("      Osoba szuka produktu z kategorii: " + product_category)

                        products_that_slave_can_afford_atm = self._product_repository.find_by_category_and_max_price(product_category, slave.account_balance)
                        num_of_that_products = len(products_that_slave_can_afford_atm)
                        if num_of_that_products == 0:
                            print("      Brak produktów na które osoba może sobie pozwolić w tym momencie.")

                        elif num_of_that_products == 1:
                            print("      Jest jeden produkt na który osoba może sobie pozwolić w tym momencie.")
                            product_to_buy = products_that_slave_can_afford_atm[0]
                            print("        " + repr(product_to_buy))

                            purchase_result = slave.buy_or_not_to_buy(product_to_buy)

                            if purchase_result == "BUY":
                                print("        Osoba kupiła produkt !")
                            else:
                                print("        Osoba zdecydowała się jednak go nie kupować...")

                        else:
                            print("      Jest wiele produktów na które osoba może sobie pozwolić " + "[" + str(num_of_that_products) + "]")
                            product_to_buy = \
                                products_that_slave_can_afford_atm[random.randint(0, num_of_that_products - 1)]

                            print("        Osoba bieże pod uwage tylko tą jedną: " + repr(product_to_buy))

                            purchase_result = slave.buy_or_not_to_buy(product_to_buy)

                            if purchase_result == "BUY":
                                print("        Osoba kupiła produkt !")
                            else:
                                print("        Osoba zdecydowała się jednak go nie kupować...")

                    print("    Osoba skończyła zakupy")
                    print("    Stan osoby: " + repr(slave))
                else:
                    print("    Osoba nie poszła do sklepu...")

                self._actual_date += _day
            print("Koniec świata dla osoby o id: " + slave.id)

    def reset(self):
        print("Reset świata")
        self._actual_date = self._start_date

    def _will_go_to_shop(self):
        event = self._get_actual_event()

        if event is None:
            return random.random() <= self._regular_go_to_shop_probability
        else:
            gts_multiplier = event.go_to_shop_probability_multiplier
            print("    [bonus prawdopodobienstwa x" + str(gts_multiplier) + " !]")
            bonus_probability = self._regular_go_to_shop_probability * gts_multiplier
            print("    prawdopodobieństwo po bonusie wynosi: " + str(bonus_probability))

            if bonus_probability >= 1.0:
                print("    Napewno pójdzie do sklepu")
                return True
            else:
                return random.random() <= bonus_probability

    def _get_actual_event(self):
        for event in self._events:
            if event.is_event_date(self._actual_date):
                return event

        return None






class Configuration:
    def __init__(self, global_settings, profiles, product_repository):
        self.global_settings = global_settings
        self.profiles = profiles
        self.product_repository = product_repository


class GlobalSettings:
    def __init__(self, start_month, end_month, year, population, daily_go_to_shop_probability, events):
        self.events = events
        self.daily_go_to_shop_probability = daily_go_to_shop_probability
        self.population = population
        self.year = year
        self.end_month = end_month
        self.start_month = start_month


class Profile:
    def __init__(self, name, percent_of_people, salary_from, salary_to, needs):
        self.salary_to = salary_to
        self.salary_from = salary_from
        self.percent_of_people = percent_of_people
        self.name = name
        self.needs = needs


class Event:
    def __init__(self, day_from, month_from, day_to, month_to, year, go_to_shop_probability_multiplier, buy_item_probability_multiplier):
        self.buy_item_probability_multiplier = buy_item_probability_multiplier
        self.go_to_shop_probability_multiplier = go_to_shop_probability_multiplier
        self._first_day = datetime.date(year, month_from, day_from)
        self._last_day = datetime.date(year, month_to, day_to)

    def is_event_date(self, date):
        return self._first_day <= date <= self._last_day


class Need:
    def __init__(self, category, num_of_items, priority, indecision_factor):
        self.indecision_factor = indecision_factor
        self.priority = priority
        self.num_of_items = num_of_items
        self.category = category

    def __repr__(self):
        return "[" + self.category + ", " + str(self.num_of_items) + ", " + str(self.priority) + ", " + str(self.indecision_factor) + "]"
