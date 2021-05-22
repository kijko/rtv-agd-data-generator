import datetime
import calendar
import random
import queue

_day = datetime.timedelta(days=1)


class Matrix:

    def __init__(self, config, event_handler):
        self._event_handler = event_handler
        self.config = config
        self.groups = _create_groups(config.global_settings.population, config.profiles)

    def run(self):
        world = World(
            self.config.global_settings.start_month,
            self.config.global_settings.end_month,
            self.config.global_settings.year,
            self.config.global_settings.events,
            self.config.product_repository
        )
        for group in self.groups:

            print("Uruchomiono symulacje dla grupy: " + group.name)
            while group.has_next_person():
                person = group.next_person()

                self._event_handler.person_was_born(person)

                world.start(person)
                world.reset()


class Group:
    def __init__(self, name, population, salary_from, salary_to, needs, go_to_shop_probability):
        self._salary_to = salary_to
        self._salary_from = salary_from
        self._max_population = population
        self._actual_population = 0
        self.needs = needs
        self.name = name
        self.go_to_shop_probability = go_to_shop_probability

    def has_next_person(self):
        return self._actual_population < self._max_population

    def next_person(self):
        if self.has_next_person():
            self._actual_population += 1

            return Person(self._actual_population, self, random.randint(self._salary_from, self._salary_to), self.needs)
        else:
            return None


class Person:
    def __init__(self, number_in_group, group, salary, needs):
        self.id = group.name + "-" + str(number_in_group)

        self._salary = salary
        self.needs = needs

        self.account_balance = 0.0
        self.go_to_shop_probability = group.go_to_shop_probability

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

    def buy_or_not_to_buy(self, product, special_event_multiplier):
        need_of_product = list(filter(lambda need: need.category == product.category, self.needs.copy()))[0]

        buy_probability = need_of_product.buy_probability
        if special_event_multiplier is not None:
            print("      Prawdopodobieństwo kupna przedmiotu x" + str(special_event_multiplier))

            calculated_buy_prob = buy_probability * special_event_multiplier
            if calculated_buy_prob >= 1.0:
                buy_probability = 1.0
            else:
                buy_probability = calculated_buy_prob

        print("      Prawdopodobieństwo kupna przedmiotu wynosi: " + str(buy_probability))

        if random.random() <= buy_probability:
            self._satisfy_need(product, need_of_product)

            return "BUY"
        else:
            return "NOT_TO_BUY"

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
                profile.needs,
                profile.go_to_shop_probability
            )
        )

    return groups


class World:
    def __init__(self, start_month, end_month, year, events, product_repository):
        self._start_date = datetime.date(year, start_month, 1)
        self._last_day_date = datetime.date(year, end_month, calendar.monthrange(year, end_month)[1])
        self._actual_date = self._start_date
        self._events = events
        self._product_repository = product_repository

    def start(self, person):
        if self._actual_date == self._last_day_date:
            print("Świat się zakończył. Zresetuj go")
        else:
            needStr = ""
            for need in person.needs:
                needStr += "[" + need.category + ", " + str(need.num_of_items) + ", " + str(need.priority) + ", " + str(need.buy_probability) + "] "

            print("Osoba z id: " + person.id + " i potrzebami: " + needStr + "została umieszona w symulacji.")

            while self._actual_date <= self._last_day_date:
                actual_date_str = self._actual_date.strftime("%d-%m-%y")
                print("  Dzień " + actual_date_str + " zaczął się.")

                if self._actual_date.day == 1:
                    person.pay_the_paycheck()
                    print("    [Wypłata ! Aktualna kwota jaką posiada osoba: " + str(person.account_balance) + "]")

                print("    Prawdopodobieństwo pójścia do sklepu wynosi: " + str(person.go_to_shop_probability))
                if self._will_go_to_shop(person):
                    print("    Osoba poszła do sklepu !")
                    print("    Stan osoby: " + repr(person))
                    shopping_list = person.prepare_shopping_list()
                    buy_probability_bonus_multiplier = self._get_bonus_buy_probability_multiplier()

                    while not shopping_list.empty():
                        product_category = shopping_list.get()
                        print("      Osoba szuka produktu z kategorii: " + product_category)

                        products_that_person_can_afford_atm = self._product_repository.find_by_category_and_max_price(product_category, person.account_balance)
                        num_of_that_products = len(products_that_person_can_afford_atm)
                        if num_of_that_products == 0:
                            print("      Brak produktów na które osoba może sobie pozwolić w tym momencie.")

                        elif num_of_that_products == 1:
                            print("      Jest jeden produkt na który osoba może sobie pozwolić w tym momencie.")
                            product_to_buy = products_that_person_can_afford_atm[0]
                            print("        " + repr(product_to_buy))

                            purchase_result = person.buy_or_not_to_buy(product_to_buy, buy_probability_bonus_multiplier)

                            if purchase_result == "BUY":
                                print("        Osoba kupiła produkt !")
                            else:
                                print("        Osoba zdecydowała się jednak go nie kupować...")

                        else:
                            print("      Jest wiele produktów na które osoba może sobie pozwolić " + "[" + str(num_of_that_products) + "]")
                            product_to_buy = \
                                products_that_person_can_afford_atm[random.randint(0, num_of_that_products - 1)]

                            print("        Osoba bieże pod uwage tylko tą jedną: " + repr(product_to_buy))

                            purchase_result = person.buy_or_not_to_buy(product_to_buy, buy_probability_bonus_multiplier)

                            if purchase_result == "BUY":
                                print("        Osoba kupiła produkt !")
                            else:
                                print("        Osoba zdecydowała się jednak go nie kupować...")

                    print("    Osoba skończyła zakupy")
                    print("    Stan osoby: " + repr(person))
                else:
                    print("    Osoba nie poszła do sklepu...")

                self._actual_date += _day
            print("Koniec świata dla osoby o id: " + person.id)

    def reset(self):
        print("Reset świata")
        self._actual_date = self._start_date

    def _will_go_to_shop(self, person):
        event = self._get_actual_event()

        if event is None:
            return random.random() <= person.go_to_shop_probability
        else:
            gts_multiplier = event.go_to_shop_probability_multiplier
            print("    [bonus prawdopodobienstwa x" + str(gts_multiplier) + " !]")
            bonus_probability = person.go_to_shop_probability * gts_multiplier
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

    def _get_bonus_buy_probability_multiplier(self):
        event = self._get_actual_event()

        if event is None:
            return None
        else:
            return event.buy_item_probability_multiplier


class Configuration:
    def __init__(self, global_settings, profiles, product_repository):
        self.global_settings = global_settings
        self.profiles = profiles
        self.product_repository = product_repository


class GlobalSettings:
    def __init__(self, start_month, end_month, year, population, events):
        self.events = events
        self.population = population
        self.year = year
        self.end_month = end_month
        self.start_month = start_month


class Profile:
    def __init__(self, name, percent_of_people, salary_from, salary_to, needs, go_to_shop_probability):
        self.salary_to = salary_to
        self.salary_from = salary_from
        self.percent_of_people = percent_of_people
        self.go_to_shop_probability = go_to_shop_probability
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
    def __init__(self, category, num_of_items, priority, buy_probability):
        self.buy_probability = buy_probability
        self.priority = priority
        self.num_of_items = num_of_items
        self.category = category

    def __repr__(self):
        return "[" + self.category + ", " + str(self.num_of_items) + ", " + str(self.priority) + ", " + str(self.buy_probability) + "]"


class MatrixEventHandler:
    def person_was_born(self, person):
        pass

    def day_begins(self, sim_datetime):
        pass

    def payday(self, person, sim_datetime):
        pass

    def went_to_shop(self, person, sim_datetime):
        pass

    def do_not_went_to_shop(self, person, sim_datetime):
        pass

    def shopping(self, person, sim_datetime, bought_products):
        pass

    def bought_nothing(self, person, sim_datetime):
        pass

    def person_died(self, person_data):
        pass

