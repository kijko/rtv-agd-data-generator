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
            self.config.global_settings.date_probability_bonuses,
            self.config.product_repository,
            self.config.global_settings.needs_associations
        )
        for group in self.groups:

            print("Uruchomiono symulacje dla grupy: " + group.name)
            while group.has_next_person():
                person = group.next_person()

                self._event_handler.person_was_born(person)

                world.start(person)
                world.reset()


class Group:
    def __init__(self, name, population, initial_account_balance, salary_from, salary_to, needs, go_to_shop_probability):
        self.initial_account_balance = initial_account_balance
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

            return Person(self._actual_population, self, random.randint(self._salary_from, self._salary_to), self.needs, self.initial_account_balance)
        else:
            return None


class Person:
    def __init__(self, number_in_group, group, salary, needs, account_balance):
        self.id = group.name + "-" + str(number_in_group)

        self._salary = salary
        self.needs = needs

        self.account_balance = account_balance
        self.go_to_shop_probability = group.go_to_shop_probability
        self._belongings = []

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

    def take_shopping_cart(self):
        return ShoppingCart()

    def calculate_remaining_budget(self, shopping_cart):
        remaining_budget = self.account_balance - shopping_cart.cost()

        if remaining_budget <= 0.0:
            return 0.0
        else:
            return remaining_budget

    def does_he_want_it(self, product, probability_multiplier):
        need_of_product = list(filter(lambda need: need.category == product.category, self.needs.copy()))[0]

        buy_probability = need_of_product.buy_probability
        if probability_multiplier is not None:
            print("        Bonus ! Prawdopodobieństwo kupna przedmiotu x" + str(probability_multiplier))

            calculated_buy_prob = buy_probability * probability_multiplier
            if calculated_buy_prob >= 1.0:
                buy_probability = 1.0
            else:
                buy_probability = calculated_buy_prob

        print("        Prawdopodobieństwo kupna przedmiotu wynosi: " + str(buy_probability))

        return random.random() <= buy_probability

    def does_he_need_associated_product(self, association, shopping_cart):
        a = association.product_category_a
        b = association.product_category_b
        relation_between_them = association.relation

        if relation_between_them == one_to_one:
            print("            Relacja pomiędzy " + a + " i " + b + ": Jeden do jednego")
            num_of_a_we_have = self._count_belongings_include_shopping_cart_by_category(a, shopping_cart)
            num_of_b_we_have = self._count_belongings_include_shopping_cart_by_category(b, shopping_cart)

            print("            Osoba posiada " + str(num_of_a_we_have) + " produktów z kategorii " + a + " oraz " + str(num_of_b_we_have) + " produktów z kategorii " + b)

            have = num_of_b_we_have < num_of_a_we_have
            if have:
                print("            Osoba uznaje że potrzebuje produkt z kategorii " + b)
            else:
                print("            Osoba uznaje, że nie potrzebuje produktu z kategorii " + b + " ponieważ już go posiada (w domu lub w koszyku)")

            return have
        else: # one to many todo
            print("            Relacja pomiędzy " + a + " i " + b + ": Jeden do wielu")
            num_of_b_we_have = self._count_belongings_include_shopping_cart_by_category(b, shopping_cart)

            return num_of_b_we_have == 0

    def _count_belongings_include_shopping_cart_by_category(self, category, shopping_cart):
        list_copy = self._belongings.copy()
        list_copy.extend(shopping_cart.products)

        return len(list(filter(lambda product: product.category == category, list_copy)))

    def does_he_want_associated_product(self, association, probability_multiplier):
        buy_probability = association.buy_probability
        if probability_multiplier is not None:
            print("        Bonus ! Prawdopodobieństwo kupna przedmiotu x" + str(probability_multiplier))

            calculated_buy_prob = buy_probability * probability_multiplier
            if calculated_buy_prob >= 1.0:
                buy_probability = 1.0
            else:
                buy_probability = calculated_buy_prob

        print("        Prawdopodobieństwo kupna przedmiotu wynosi: " + str(buy_probability))

        return random.random() <= buy_probability

    def buy_things(self, shopping_cart):
        for needed_product in shopping_cart.needed_products:
            self._buy(needed_product)
            self._satisfy_need(needed_product)

        for not_needed_product in shopping_cart.not_needed_products:
            self._buy(not_needed_product)

    def _satisfy_need(self, product):
        need_of_product = list(filter(lambda need: need.category == product.category, self.needs.copy()))[0]

        if need_of_product.num_of_items > 1:
            need_of_product.num_of_items -= 1
        else:
            self.needs = list(filter(lambda need: need.category != need_of_product.category, self.needs.copy()))

    def _buy(self, product):
        self.account_balance -= product.price
        self._belongings.append(product)

    def __repr__(self):
        needs_str = "["

        for need in self.needs:
            needs_str += repr(need) + ", "

        needs_str += "]"

        belongings_str = "["

        for product in self._belongings:
            belongings_str += repr(product) + ", "

        belongings_str += "]"


        return "Osoba: [id=" + self.id + ", salary=" + str(self._salary) + ", needs=" + needs_str + ", acc_balance=" + str(self.account_balance) + ", belongings=" + belongings_str + "]"


class ShoppingCart:
    def __init__(self):
        self.products = []
        self.needed_products = []
        self.not_needed_products = []

    def cost(self):
        products_cost = 0.0
        for product in self.products:
            products_cost += product.price

        return products_cost

    def place_needed_product(self, product):
        self.products.append(product)
        self.needed_products.append(product)

    def place_not_needed_product(self, product):
        self.products.append(product)
        self.not_needed_products.append(product)


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
                profile.initial_account_balance,
                profile.salary_from,
                profile.salary_to,
                profile.needs,
                profile.go_to_shop_probability
            )
        )

    return groups


class World:
    def __init__(self, start_month, end_month, year, date_probability_bonuses, product_repository, needs_associations):
        self._start_date = datetime.date(year, start_month, 1)
        self._last_day_date = datetime.date(year, end_month, calendar.monthrange(year, end_month)[1])
        self._actual_date = self._start_date
        self._date_probability_bonuses = date_probability_bonuses
        self._product_repository = product_repository # todo move to persuader
        self._needs_associations = needs_associations

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

                    shopping_cart = person.take_shopping_cart()

                    while not shopping_list.empty():
                        product_category = shopping_list.get()
                        print("      Osoba szuka produktu z kategorii: " + product_category)

                        remaining_budget = person.calculate_remaining_budget(shopping_cart)
                        products_that_person_can_afford_atm = \
                            self._product_repository.find_by_category_and_max_price(product_category, remaining_budget)
                        num_of_that_products = len(products_that_person_can_afford_atm)
                        if num_of_that_products > 0:
                            product_to_buy = None

                            if num_of_that_products == 1:
                                print("      Jest jeden produkt na który osoba może sobie pozwolić w tym momencie.")
                                product_to_buy = products_that_person_can_afford_atm[0]
                                print("        " + repr(product_to_buy))
                            else:
                                print("      Jest wiele produktów na które osoba może sobie pozwolić " + "[" + str(num_of_that_products) + "]")
                                product_to_buy = \
                                    products_that_person_can_afford_atm[random.randint(0, num_of_that_products - 1)]
                                print("        Osoba bieże pod uwage tylko ten jeden: " + repr(product_to_buy))

                            if person.does_he_want_it(product_to_buy, buy_probability_bonus_multiplier):
                                shopping_cart.place_needed_product(product_to_buy)
                                print("        Osoba umieściła produkt w koszyku!")

                                self._on_product_bought(person, shopping_cart, product_to_buy, buy_probability_bonus_multiplier)
                            else:
                                print("        Osoba zrezygnowała z kupna przedmiotu...")

                        else:
                            print("      Brak produktów na które osoba może sobie pozwolić w tym momencie.")

                    print("    Osoba idzie do kasy...")
                    person.buy_things(shopping_cart)
                    print("    Osoba zakończyła zakupy")
                    print("    Stan osoby: " + repr(person))
                else:
                    print("    Osoba nie poszła do sklepu...")

                self._actual_date += _day
            print("Koniec świata dla osoby o id: " + person.id)

    def _on_product_bought(self, person, shopping_cart, bought_product, buy_prob_bonus_multiplier):
        print("          Wyszukiwanie silnych powiązań dla kategorii: " + bought_product.category)
        strong_associations = self._find_strong_associations_for_prod_category(bought_product.category)

        if len(strong_associations) > 0:
            associated_categories_str = ", ".join(map(lambda associ: associ.product_category_b, strong_associations))
            print("          Znaleziono powiązania z kategoriami: " + associated_categories_str)

            for ass in strong_associations:
                associated_category = ass.product_category_b
                print("          Analiza powiązania z kategorią: " + associated_category)
                remaining_budget = person.calculate_remaining_budget(shopping_cart)

                if person.does_he_need_associated_product(ass, shopping_cart):
                    print("          Osoba potrzebuje produktu z silnie powiązanej kategorii " + associated_category)
                    print("          I jej budżet wynosi: " + str(remaining_budget))

                    associated_category_products_that_person_can_afford_atm = \
                        self._product_repository.find_by_category_and_max_price(associated_category, remaining_budget)
                    num_of_that_products = len(associated_category_products_that_person_can_afford_atm)

                    if num_of_that_products > 0:
                        print("          Znaleziono " + str(num_of_that_products) + " produktów z powiązanej kategorii")
                        product_index = random.randint(0, num_of_that_products - 1)
                        product_to_buy = associated_category_products_that_person_can_afford_atm[product_index]

                        print("          Wybrano produkt: " + repr(product_to_buy))

                        if person.does_he_want_associated_product(ass, buy_prob_bonus_multiplier):
                            print("          Kupuje to !")
                            shopping_cart.place_not_needed_product(product_to_buy)

                            print("          Wyszukiwanie dalszych powiązań dla kategorii: " + product_to_buy.category)
                            self._on_product_bought(person, shopping_cart, product_to_buy, buy_prob_bonus_multiplier)
                        else:
                            print("          Osoba zdecydowała się jednak go nie kupować...")

                    else:
                        print("          Nie znaleziono produktów z kategorii " + associated_category)

                else:
                    print("          Osoba niepotrzebuje produktu z silnie powiązanej kategorii " + associated_category)


        else:
            print("          Brak silnie powiązanych produktów dla kategorii " + bought_product.category)

    def _find_strong_associations_for_prod_category(self, category):
        list_copy = self._needs_associations.copy()

        return list(filter(lambda association: association.product_category_a == category, list_copy))

    def reset(self):
        print("Reset świata")
        self._actual_date = self._start_date

    def _will_go_to_shop(self, person):
        bonus = self._get_actual_bonus()

        if bonus is None:
            return random.random() <= person.go_to_shop_probability
        else:
            gts_multiplier = bonus.go_to_shop_probability_multiplier
            print("    [bonus prawdopodobienstwa x" + str(gts_multiplier) + " !]")
            bonus_probability = person.go_to_shop_probability * gts_multiplier
            print("    prawdopodobieństwo po bonusie wynosi: " + str(bonus_probability))

            if bonus_probability >= 1.0:
                print("    Napewno pójdzie do sklepu")
                return True
            else:
                return random.random() <= bonus_probability

    def _get_actual_bonus(self):
        for bonus in self._date_probability_bonuses:
            if bonus.date_has_bonus(self._actual_date):
                return bonus

        return None

    def _get_bonus_buy_probability_multiplier(self):
        bonus = self._get_actual_bonus()

        if bonus is None:
            return None
        else:
            return bonus.buy_item_probability_multiplier


class Configuration:
    def __init__(self, global_settings, profiles, product_repository):
        self.global_settings = global_settings
        self.profiles = profiles
        self.product_repository = product_repository


class GlobalSettings:
    def __init__(self, start_month, end_month, year, population, date_probability_bonuses, needs_associations):
        self.needs_associations = needs_associations
        self.date_probability_bonuses = date_probability_bonuses
        self.population = population
        self.year = year
        self.end_month = end_month
        self.start_month = start_month


class Profile:
    def __init__(self, name, percent_of_people, initial_account_balance, salary_from, salary_to, needs, go_to_shop_probability):
        self.initial_account_balance = initial_account_balance
        self.salary_to = salary_to
        self.salary_from = salary_from
        self.percent_of_people = percent_of_people
        self.go_to_shop_probability = go_to_shop_probability
        self.name = name
        self.needs = needs


class DateProbabilityBonus:
    def __init__(self, day_from, month_from, day_to, month_to, year, go_to_shop_probability_multiplier, buy_item_probability_multiplier):
        self.buy_item_probability_multiplier = buy_item_probability_multiplier
        self.go_to_shop_probability_multiplier = go_to_shop_probability_multiplier
        self._first_day = datetime.date(year, month_from, day_from)
        self._last_day = datetime.date(year, month_to, day_to)

    def date_has_bonus(self, date):
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


one_to_one = "ONE_TO_ONE"
one_to_many = "ONE_TO_MANY"


class StrongAssociation:
    def __init__(self, product_category_a, product_category_b, relation, buy_probability):
        self.buy_probability = buy_probability
        self.relation = relation
        self.product_category_b = product_category_b
        self.product_category_a = product_category_a

