import datetime
import calendar
import random
import queue
import uuid
import yaml
from error import ValidationError

_day = datetime.timedelta(days=1)


def _date_str(date):
    return date.strftime("%d-%m-%y")


class Matrix:

    def __init__(self, config, event_handler, progress_handler):
        self._progress_handler = progress_handler
        self._event_handler = event_handler
        self.config = config
        self.groups = _create_groups(config.global_settings.population, config.profiles)
        self._person_counter = 0

    def run(self, stopper):
        world = World(
            self.config.global_settings.start_month,
            self.config.global_settings.start_year,
            self.config.global_settings.end_month,
            self.config.global_settings.end_year,
            self.config.global_settings.date_probability_bonuses,
            self.config.product_repository,
            self.config.global_settings.needs_associations,
            self._event_handler
        )

        self._progress_handler.on_start()

        actually_population = 0

        for group in self.groups:
            actually_population += group.max_population

        self._progress_handler.on_progress_change(self._person_counter, actually_population)

        if stopper.should_stop:
            # print("Zatrzymano symulacje odrazu")
            self._progress_handler.on_end()
        else:
            for group in self.groups:

                # print("Uruchomiono symulacje dla grupy: " + group.name)
                while group.has_next_person():
                    person = group.next_person()

                    self._event_handler.person_was_born(person)

                    world.start(person)
                    world.reset()

                    self._person_counter += 1
                    self._progress_handler.on_progress_change(self._person_counter, actually_population)

                    if stopper.should_stop:
                        # print("Zatrzymuje symulacje")
                        break

            self._progress_handler.on_end()



class Group:
    def __init__(self, name, population, initial_account_balance, salary_from, salary_to, needs, go_to_shop_probability):
        self.initial_account_balance = initial_account_balance
        self._salary_to = salary_to
        self._salary_from = salary_from
        self.max_population = population
        self._actual_population = 0
        self.needs = needs
        self.name = name
        self.go_to_shop_probability = go_to_shop_probability

    def has_next_person(self):
        return self._actual_population < self.max_population

    def next_person(self):
        if self.has_next_person():
            self._actual_population += 1

            return Person(self._actual_population, self, random.randint(self._salary_from, self._salary_to), self.needs, self.initial_account_balance)
        else:
            return None


class Person:
    def __init__(self, number_in_group, group, salary, needs, account_balance):
        self.id = group.name + "-" + str(number_in_group)
        self.group_name = group.name

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

    def catch_marketing_offer(self, marketing_offer):
        # print("      Wdra??anie z??apanej oferty marketingowej")

        needs_from_category = self._needs_from_category(marketing_offer.product_category)

        if len(needs_from_category) > 0:
            # print("        Osoba ma ju?? potrzeb?? kupna produktu z kategorii: " + marketing_offer.product_category)
            corresponding_need = needs_from_category[0]

            if random.random() <= 0.5:
                # print("        Prawdopodobie??stwo kupna przedmiotu zosta??o zwi??kszone o 50% !")

                half_of_prob = corresponding_need.buy_probability / 2
                new_probability = corresponding_need.buy_probability + half_of_prob

                if new_probability >= 1.0:
                    corresponding_need.buy_probability = 1.0
                else:
                    corresponding_need.buy_probability = new_probability
            else:
                # print("        Liczba przedmiot??w z kategorii " + marketing_offer.product_category + " kt??re osoba chcia??aby kupi?? zosta??a zwi??kszona o 1 !")
                corresponding_need.num_of_items += 1

        else:
            # print("        Osoba nie my??la??a wcze??niej o kupnie przedmiotu z kategorii " + marketing_offer.product_category + ". Dodawanie nowej potrzeby")
            self.needs.append(
                Need(marketing_offer.product_category, 1, random.randint(-100, 100), marketing_offer.buy_probability)
            )

    def _needs_from_category(self, category):
        return list(filter(lambda need: need.category == category, self.needs.copy()))

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
            # print("        Bonus ! Prawdopodobie??stwo kupna przedmiotu x" + str(probability_multiplier))

            calculated_buy_prob = buy_probability * probability_multiplier
            # print("DOES HE WANT IT - normal probability: " + str(buy_probability) + ", multiplier: " + str(probability_multiplier) + ", calculated: " + str(calculated_buy_prob))
            if calculated_buy_prob >= 1.0:
                buy_probability = 1.0
            else:
                buy_probability = calculated_buy_prob

        # print("        Prawdopodobie??stwo kupna przedmiotu wynosi: " + str(buy_probability))

        return random.random() <= buy_probability

    def does_he_need_associated_product(self, association, shopping_cart):
        a = association.product_category_a
        b = association.product_category_b
        relation_between_them = association.relation

        if relation_between_them == one_to_one:
            # print("            Relacja pomi??dzy " + a + " i " + b + ": Jeden do jednego")
            num_of_a_we_have = self._count_belongings_include_shopping_cart_by_category(a, shopping_cart)
            num_of_b_we_have = self._count_belongings_include_shopping_cart_by_category(b, shopping_cart)

            # print("            Osoba posiada " + str(num_of_a_we_have) + " produkt??w z kategorii " + a + " oraz " + str(num_of_b_we_have) + " produkt??w z kategorii " + b)

            have = num_of_b_we_have < num_of_a_we_have
            if have:
                pass
                # print("            Osoba uznaje ??e potrzebuje produkt z kategorii " + b)
            else:
                pass
                # print("            Osoba uznaje, ??e nie potrzebuje produktu z kategorii " + b + " poniewa?? ju?? go posiada (w domu lub w koszyku)")

            return have
        else:
            # print("            Relacja pomi??dzy " + a + " i " + b + ": Jeden do wielu")
            num_of_b_we_have = self._count_belongings_include_shopping_cart_by_category(b, shopping_cart)

            return num_of_b_we_have == 0

    def _count_belongings_include_shopping_cart_by_category(self, category, shopping_cart):
        list_copy = self._belongings.copy()
        list_copy.extend(shopping_cart.products)

        return len(list(filter(lambda product: product.category == category, list_copy)))

    def does_he_want_associated_product(self, association, probability_multiplier):
        buy_probability = association.buy_probability
        if probability_multiplier is not None:
            # print("        Bonus ! Prawdopodobie??stwo kupna przedmiotu x" + str(probability_multiplier))

            calculated_buy_prob = buy_probability * probability_multiplier
            # print("DOES HE WANT ASSOCIATED: bonus prob: " + str(association.buy_probability) + ", multiplier: " + str(probability_multiplier) + ", calc: " + str(calculated_buy_prob))
            if calculated_buy_prob >= 1.0:
                buy_probability = 1.0
            else:
                buy_probability = calculated_buy_prob

        # print("        Prawdopodobie??stwo kupna przedmiotu wynosi: " + str(buy_probability))

        return random.random() <= buy_probability

    def buy_things(self, shopping_cart):
        for product in shopping_cart.products:
            self._buy(product)
            self._satisfy_need(product)

    def _satisfy_need(self, product):
        found_needs = list(filter(lambda need: need.category == product.category, self.needs.copy()))

        if len(found_needs) > 0:
            need_of_product = found_needs[0]

            if need_of_product.num_of_items > 1:
                need_of_product.num_of_items -= 1
            else:
                self.needs = list(filter(lambda need: need.category != need_of_product.category, self.needs.copy()))
        else:
            pass


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


class ConsideringContext:
    def __init__(self, products, person, shopping_cart, buy_probability_bonus_multiplier):
        self.products = products
        self.buy_probability_bonus_multiplier = buy_probability_bonus_multiplier
        self.shopping_cart = shopping_cart
        self.person = person

    def recreate_with_other_products(self, products):
        return ConsideringContext(products, self.person, self.shopping_cart, self.buy_probability_bonus_multiplier)


class MarketingOffer:
    def __init__(self, product_category, catch_probability, buy_probability):
        self.buy_probability = buy_probability
        self.catch_probability = catch_probability
        self.product_category = product_category

    def __repr__(self):
        return "MarketingOffer_[" + self.product_category + ", " + str(self.catch_probability) + ", " + str(self.buy_probability) + "]"


class NotificationBox:
    def __init__(self):
        self._date_to_notifications = {}

    def flush(self):
        self._date_to_notifications.clear()

    def get_for_date(self, date):
        key = _date_str(date)

        if key in self._date_to_notifications:
            return self._date_to_notifications.pop(key)
        else:
            return None

    def show_on_time(self, date, offer):
        key = _date_str(date)

        if key in self._date_to_notifications:
            self._date_to_notifications[key].append(offer)
        else:
            self._date_to_notifications[key] = [offer]

        # print("    Oferta marketingowa przygotowana do wys??ania ", self._date_to_notifications)


class World:
    def __init__(self, start_month, start_year, end_month, end_year, date_probability_bonuses, product_repository, needs_associations, event_handler):
        self._event_handler = event_handler
        self._start_date = datetime.date(start_year, start_month, 1)
        self._last_day_date = datetime.date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
        self._actual_date = self._start_date
        self._date_probability_bonuses = date_probability_bonuses
        self._product_repository = product_repository
        self._needs_associations = needs_associations
        self._notification_box = NotificationBox()

    def start(self, person):
        if self._actual_date == self._last_day_date:
            pass
            # print("??wiat si?? zako??czy??. Zresetuj go")
        else:
            needStr = ""
            for need in person.needs:
                needStr += "[" + need.category + ", " + str(need.num_of_items) + ", " + str(need.priority) + ", " + str(need.buy_probability) + "] "

            # print("Osoba z id: " + person.id + " i potrzebami: " + needStr + "zosta??a umieszona w symulacji.")

            while self._actual_date <= self._last_day_date:
                actual_date_str = _date_str(self._actual_date)
                # print("  Dzie?? " + actual_date_str + " zacz???? si??.")

                if self._actual_date.day == 1:
                    person.pay_the_paycheck()
                    # print("    [Wyp??ata ! Aktualna kwota jak?? posiada osoba: " + str(person.account_balance) + "]")

                self._process_notifications(person)

                # print("    Prawdopodobie??stwo p??j??cia do sklepu wynosi: " + str(person.go_to_shop_probability))
                if self._will_go_to_shop(person):
                    visit_id = str(uuid.uuid4())
                    self._event_handler.went_to_shop(person, self._actual_date, visit_id)

                    # print("    Osoba posz??a do sklepu !")
                    # print("    Stan osoby: " + repr(person))
                    shopping_list = person.prepare_shopping_list()
                    buy_probability_bonus_multiplier = self._get_bonus_buy_probability_multiplier()

                    shopping_cart = person.take_shopping_cart()

                    while not shopping_list.empty():
                        product_category = shopping_list.get()
                        # print("      Osoba szuka produktu z kategorii: " + product_category)

                        remaining_budget = person.calculate_remaining_budget(shopping_cart)
                        products_that_person_can_afford_atm = \
                            self._product_repository.find_by_category_and_max_price(product_category, remaining_budget)
                        num_of_that_products = len(products_that_person_can_afford_atm)
                        if num_of_that_products > 0:
                            product_to_buy = None

                            if num_of_that_products == 1:
                                # print("      Jest jeden produkt na kt??ry osoba mo??e sobie pozwoli?? w tym momencie.")
                                product_to_buy = products_that_person_can_afford_atm[0]
                                # print("        " + repr(product_to_buy))
                            else:
                                # print("      Jest wiele produkt??w na kt??re osoba mo??e sobie pozwoli?? " + "[" + str(num_of_that_products) + "]")
                                product_to_buy = \
                                    products_that_person_can_afford_atm[random.randint(0, num_of_that_products - 1)]
                                # print("        Osoba bie??e pod uwage tylko ten jeden: " + repr(product_to_buy))

                            if person.does_he_want_it(product_to_buy, buy_probability_bonus_multiplier):
                                shopping_cart.place_needed_product(product_to_buy)
                                # print("        Osoba umie??ci??a produkt w koszyku!")

                                self._consider_associated_products_purchase(
                                    StrongAssociation,
                                    ConsideringContext([product_to_buy], person, shopping_cart, buy_probability_bonus_multiplier)
                                )
                            else:
                                pass
                                # print("        Osoba zrezygnowa??a z kupna przedmiotu...")

                        else:
                            pass
                            # print("      Brak produkt??w na kt??re osoba mo??e sobie pozwoli?? w tym momencie.")

                    # print("    Osoba idzie do kasy...")

                    # print("    Kasjer proponuje co mu kazali")
                    self._consider_associated_products_purchase(
                        Association,
                        ConsideringContext(shopping_cart.products, person, shopping_cart, buy_probability_bonus_multiplier)
                    )

                    person.buy_things(shopping_cart)

                    self._event_handler.shopping(person, self._actual_date, shopping_cart.products.copy(), visit_id)

                    # print("    Osoba zako??czy??a zakupy")

                    # print("    Przetwarzanie zakupionych produkt??w w celu wysy??ki powi??zanych propozycji/promocji kana??ami marketingowymi")
                    self._process_bought_products(shopping_cart)

                    # print("    Stan osoby: " + repr(person))
                else:
                    pass
                    # print("    Osoba nie posz??a do sklepu...")

                self._actual_date += _day
            # print("Koniec ??wiata dla osoby o id: " + person.id)
            self._event_handler.person_died(person)

    def _process_notifications(self, person):
        # print("    Przetwarzanie otrzymanych ofert")

        notifications = self._notification_box.get_for_date(self._actual_date)

        if notifications is None:
            pass
            # print("    Brak ofert")

        else:
            # print("    Otrzymano " + str(len(notifications)) + " ofert marketingowych")

            for notification in notifications:
                # print("      Przetwarzanie oferty: " + repr(notification))
                if random.random() <= notification.catch_probability:
                    # print("    Osoba z??apa??a przyn??te !")
                    person.catch_marketing_offer(notification)
                else:
                    pass
                    # print("    Osoba nie jest zainteresowana ofert??")

    def _process_bought_products(self, shopping_cart):
        for product in shopping_cart.products:
            # print("      Wyszukiwanie powi??za?? " + str(LooselyCoupledAssociation) + " dla produktu: " + repr(product))
            loosely_coupled_associations = \
                self._find_associations_by_product_category_and_association_type(product.category, LooselyCoupledAssociation)
            num_of_asses = len(loosely_coupled_associations)

            if num_of_asses > 0:
                # print("        Znaleziono " + str(num_of_asses) + " powi??za??. Przygotowywanie oferty marketingowej")

                for ass in loosely_coupled_associations:
                    # print("    Przetwarzanie powi??zania " + str(LooselyCoupledAssociation))
                    one_to_seven_days = _day * random.randint(1, 7)

                    date_when_person_receive_offer = \
                        datetime.date(self._actual_date.year, self._actual_date.month, self._actual_date.day) \
                        + one_to_seven_days
                    offer = MarketingOffer(
                        ass.product_category_b,
                        ass.need_probability,
                        ass.buy_probability
                    )

                    self._notification_box.show_on_time(date_when_person_receive_offer, offer)

                    # print("        Wys??ano ofert?? marketingow??: " + repr(offer))

                    date_when_person_receive_offer_str = _date_str(date_when_person_receive_offer)
                    # print("        Zostanie ona odebrana przez osob?? dnia: " + date_when_person_receive_offer_str)

            else:
                pass
                # print("        Brak powi??za??.")

    # association_type -> only types that inherit from ShoppingStageAssociation
    def _consider_associated_products_purchase(self, association_type, considering_context):
        # print("          Analiza powi??zanych kategorii dla produkt??w: " + ", ".join(map(lambda prd: repr(prd), considering_context.products)))
        # print("          Typ powi??zania: " + str(association_type))

        for product in considering_context.products:
            # print("          Analiza powi??za?? dla produktu: " + repr(product))
            associations = \
                self._find_associations_by_product_category_and_association_type(product.category, association_type)
            num_of_associations = len(associations)

            if num_of_associations > 0:
                associated_categories_str = ", ".join(map(lambda associ: associ.product_category_b, associations))
                # print("          Znaleziono powi??zania z kategoriami: " + associated_categories_str)

                for ass in associations:
                    associated_category = ass.product_category_b

                    # print("          Analiza powi??zania z kategori??: " + associated_category)

                    person = considering_context.person
                    shopping_cart = considering_context.shopping_cart
                    remaining_budget = person.calculate_remaining_budget(shopping_cart)

                    if person.does_he_need_associated_product(ass, shopping_cart):
                        # print("          Osoba potrzebuje produktu z powi??zanej kategorii " + associated_category)
                        # print("          Aktualny bud??et wynosi: " + str(remaining_budget))

                        associated_category_products_that_person_can_afford_atm = \
                            self._product_repository.find_by_category_and_max_price(associated_category, remaining_budget)
                        num_of_that_products = len(associated_category_products_that_person_can_afford_atm)

                        if num_of_that_products > 0:
                            # print("          Znaleziono " + str(num_of_that_products) + " produkt??w z powi??zanej kategorii")
                            product_index = random.randint(0, num_of_that_products - 1)
                            product_to_buy = associated_category_products_that_person_can_afford_atm[product_index]

                            # print("          Wybrano produkt: " + repr(product_to_buy))

                            buy_prob_bonus_multiplier = considering_context.buy_probability_bonus_multiplier
                            if person.does_he_want_associated_product(ass, buy_prob_bonus_multiplier):
                                # print("          Kupuje to !")
                                shopping_cart.place_not_needed_product(product_to_buy)

                                # print("          Wyszukiwanie dalszych powi??za?? dla kategorii: " + product_to_buy.category)
                                self._consider_associated_products_purchase(
                                    association_type,
                                    considering_context.recreate_with_other_products([product_to_buy])
                                )
                            else:
                                pass
                                # print("          Osoba zdecydowa??a si?? jednak go nie kupowa??...")

                        else:
                            pass
                            # print("          Nie znaleziono produkt??w z kategorii " + associated_category)

                    else:
                        pass
                        # print("          Osoba niepotrzebuje produktu z powi??zanej kategorii " + associated_category)

            else:
                pass
                # print("          Brak powi??za?? typu: " + str(association_type) + " dla kategorii " + product.category)

    def _find_associations_by_product_category_and_association_type(self, category, association_type):
        list_copy = self._needs_associations.copy()

        return list(
            filter(
                lambda association:
                isinstance(association, association_type) and association.product_category_a == category,
                list_copy
            )
        )

    def reset(self):
        # print("Reset ??wiata")
        self._actual_date = self._start_date
        self._notification_box.flush()

    def _will_go_to_shop(self, person):
        bonus = self._get_actual_bonus()

        if bonus is None:
            return random.random() <= person.go_to_shop_probability
        else:
            gts_multiplier = bonus.go_to_shop_probability_multiplier
            # print("    [bonus prawdopodobienstwa x" + str(gts_multiplier) + " !]")
            bonus_probability = person.go_to_shop_probability * gts_multiplier
            # print("    prawdopodobie??stwo po bonusie wynosi: " + str(bonus_probability))

            # print("WILL GO TO SHOP: go to shop prob: " + str(person.go_to_shop_probability) + ", multiplier: " + str(gts_multiplier) + ", calc: " + str(bonus_probability))

            if bonus_probability >= 1.0:
                # print("    Napewno p??jdzie do sklepu")
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
        if global_settings is None or len(profiles) == 0 or profiles is None or product_repository is None:
            raise ValueError("Configuration receives incorrect objects")

        self.global_settings = global_settings
        self.profiles = profiles
        self.product_repository = product_repository

    def __repr__(self):
        return "GlobalSettings: " + repr(self.global_settings) + "\n" + "Profiles: " + repr(self.profiles) + "\n" + "Product Repo: " + repr(self.product_repository)


_month_name_to_number_dict = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12
}


def _determine_num_of_month(month_name):
    return _month_name_to_number_dict[month_name]


class YMLConfiguration(Configuration):

    def __init__(self, yml_file_path, product_repository):
        supported_version = 1
        # print("??adowanie konfiguracji z pliku: " + yml_file_path)

        global_settings = None
        profiles = []
        with open(yml_file_path, "r", encoding="utf-8") as stream:
            try:
                config_file = yaml.safe_load(stream)

                if config_file["version"] != supported_version:
                    raise ValidationError("Wersja pliku yml nie zgadza si?? z wersj?? obs??ugiwan?? przez program. Zaktualizuj program lub struktur?? pliku konfiguracyjnego. Wersja pliku: " + str(config_file["version"]) + " Wersja wspierana przez program: " + str(supported_version))

                file_global_settings = config_file["global_settings"]
                num_of_people = file_global_settings["number_of_people"]
                simulation = file_global_settings["simulation"]
                start_month = simulation["start_month"]
                start_year = simulation["start_year"]
                end_month = simulation["end_month"]
                end_year = simulation["end_year"]
                date_probability_bonuses = simulation["date_probability_bonuses"]
                needs_associations = simulation["needs_associations"]
                profiles = config_file["profiles"]

                global_settings = GlobalSettings(
                    _determine_num_of_month(start_month),
                    int(start_year),
                    _determine_num_of_month(end_month),
                    int(end_year),
                    int(num_of_people),
                    YMLConfiguration._parse_date_probability_bonuses(date_probability_bonuses),
                    YMLConfiguration._parse_needs_associations(needs_associations)
                )
                profiles = YMLConfiguration._parse_profiles(profiles)
            except Exception as exc:
                raise ValidationError(repr(exc))

            stream.close()

        # print("Za??adowano konfiguracj??: " + repr(global_settings))
        # print("Za??adowano profile: " + repr(profiles))
        super().__init__(global_settings, profiles, product_repository)

    @staticmethod
    def _parse_profiles(profiles):
        def map_to_obj(profile):
            name = profile["name"]
            percent_of_people = profile["percent_of_people"]
            daily_gts_prob = profile["daily_go_to_shop_probability"]
            init_acc_balance = profile["initial_account_balance"]
            salary_from = profile["salary"]["from"]
            salary_to = profile["salary"]["to"]
            needs = YMLConfiguration._parse_needs(profile["needs"])

            return Profile(name, int(percent_of_people), float(init_acc_balance), int(salary_from), int(salary_to), needs, float(daily_gts_prob))

        return list(map(lambda prof: map_to_obj(prof), profiles))

    @staticmethod
    def _parse_needs(needs):
        def map_to_obj(need):
            category = need["category"]
            num_of_items = need["num_of_items"]
            priority = need["priority"]
            buy_probability = need["buy_probability"]

            return Need(category, int(num_of_items), int(priority), float(buy_probability))

        return list(map(lambda need: map_to_obj(need), needs))

    @staticmethod
    def _parse_needs_associations(needs_associations):
        def map_to_object(need_ass):
            category_a = need_ass["items_from_category"]
            ass_type = need_ass["are"]
            category_b = need_ass["with"]

            if ass_type == "HIGHLY_ASSOCIATED" or ass_type == "ASSOCIATED":
                relation = need_ass["by_relation"]
                buy_probability = need_ass["with_buy_probability"]

                if ass_type == "HIGHLY_ASSOCIATED":
                    return StrongAssociation(category_a, category_b, relation, float(buy_probability))
                else:
                    return Association(category_a, category_b, relation, float(buy_probability))
            else:
                if ass_type == "LOOSELY_ASSOCIATED":
                    need_probability = need_ass["with_need_probability"]
                    buy_probability = need_ass["with_buy_probability"]

                    return LooselyCoupledAssociation(category_a, category_b, float(need_probability), float(buy_probability))
                else:
                    raise ValidationError.field_error("needs_associations.are", ass_type)

        return list(map(lambda need_ass: map_to_object(need_ass), needs_associations))

    @staticmethod
    def _parse_date_probability_bonuses(date_probability_bonuses):
        def map_to_object(bonus):
            b_from = datetime.datetime.strptime(bonus["from"], "%d.%m.%Y")
            b_to = datetime.datetime.strptime(bonus["to"], "%d.%m.%Y")
            gts_prob_multi = bonus["probability_multipliers"]["go_to_shop"]
            buy_prob_multi = bonus["probability_multipliers"]["buy_item"]

            return DateProbabilityBonus(b_from.day, b_from.month, b_from.year, b_to.day, b_to.month, b_to.year, float(gts_prob_multi), float(buy_prob_multi))

        return list(map(lambda bonus: map_to_object(bonus), date_probability_bonuses))


class GlobalSettings:
    def __init__(self, start_month, start_year, end_month, end_year, population, date_probability_bonuses, needs_associations):
        self._validate(start_month, start_year, end_month, end_year, population)

        self.end_year = end_year
        self.start_year = start_year
        self.needs_associations = needs_associations
        self.date_probability_bonuses = date_probability_bonuses
        self.population = int(population)
        self.end_month = end_month
        self.start_month = start_month


    def __repr__(self):
        return "{start_month: " + str(self.start_month) + ", start_year: " + str(self.start_year) + ", end_month: " + str(self.end_month) + ", end_year: " + str(self.end_year) + ", population: " + str(self.population) + ", date_prob_bonuses: " + repr(self.date_probability_bonuses) + ", needs_associations: " + repr(self.needs_associations) + "}"

    def _validate(self, start_month, start_year, end_month, end_year, population):
        if start_month < 1 or start_month > 12:
            raise ValidationError.field_error("start_month", start_month)

        if start_year < 1970 or start_year > end_year:
            raise ValidationError.field_error("start_year", start_year)

        if end_month < 1 or end_month > 12:
            raise ValidationError.field_error("end_month", end_month)

        if end_year < 1970 and end_year < start_year:
            raise ValidationError.field_error("end_year", end_year)

        if population < 0:
            raise ValidationError.field_error("number_of_people", population)



class Profile:
    def __init__(self, name, percent_of_people, initial_account_balance, salary_from, salary_to, needs, go_to_shop_probability):
        if initial_account_balance < 0:
            raise ValidationError.field_error("profile.initial_acc_balance", initial_account_balance)

        if percent_of_people < 0:
            raise ValidationError.field_error("profile.percent_of_people", percent_of_people)

        if salary_from < 0 or salary_from > salary_to:
            raise ValidationError.field_error("profile.salary_from", salary_from)

        if salary_to < 0 or salary_to < salary_from:
            raise ValidationError.field_error("profile.salary_to", salary_to)

        if len(needs) == 0:
            raise ValidationError.field_error("profile.needs", "!EMPTY!")

        if go_to_shop_probability < 0.0 or go_to_shop_probability > 1.0:
            raise ValidationError.field_error("profile.gotoshop_prob", go_to_shop_probability)

        if len(name.strip()) == 0:
            raise ValidationError.field_error("profile.name", "!EMPTY!")

        self.initial_account_balance = initial_account_balance
        self.salary_to = salary_to
        self.salary_from = salary_from
        self.percent_of_people = percent_of_people
        self.go_to_shop_probability = go_to_shop_probability
        self.name = name
        self.needs = needs

    def __repr__(self):
        return "Profile[name: " + self.name + ", percent_of_people: " + str(self.percent_of_people) + ", init_bank_acc: " + str(self.initial_account_balance) + ", salary_from: " + str(self.salary_from) + ", salary_to: " + str(self.salary_to) + ", needs: " + repr(self.needs) + ", go_to_shop_prob: " + str(self.go_to_shop_probability) + "]"

class DateProbabilityBonus:
    def __init__(self, day_from, month_from, year_from, day_to, month_to, year_to, go_to_shop_probability_multiplier, buy_item_probability_multiplier):
        self.year_from = year_from

        if buy_item_probability_multiplier < 0.0:
            raise ValidationError.field_error("jedno z date_probability_bonuses.probability_multipliers.buy_item", buy_item_probability_multiplier)

        if go_to_shop_probability_multiplier < 0.0:
            raise ValidationError.field_error("jedno z date_probability_bonuses.probability_multipliers.go_to_shop", go_to_shop_probability_multiplier)

        self.buy_item_probability_multiplier = buy_item_probability_multiplier
        self.go_to_shop_probability_multiplier = go_to_shop_probability_multiplier
        self._first_day = datetime.date(year_from, month_from, day_from)
        self._last_day = datetime.date(year_to, month_to, day_to)

    def date_has_bonus(self, date):
        return self._first_day <= date <= self._last_day

    def __repr__(self):
        return "DateProbBonus[" + _date_str(self._first_day) + " - " + _date_str(self._last_day) + ", buy_multiplier: " + str(self.buy_item_probability_multiplier) + ", gotoshop_multiplier: " + str(self.go_to_shop_probability_multiplier) + "]"


class Need:
    def __init__(self, category, num_of_items, priority, buy_probability):

        if buy_probability < 0.0 or buy_probability > 1.0:
            raise ValidationError.field_error("need.buy_probability", buy_probability)

        if num_of_items < 0:
            raise ValidationError.field_error("need.num_of_items", num_of_items)

        if len(category.strip()) == 0:
            raise ValidationError.field_error("need.category", "!EMPTY!")

        self.buy_probability = buy_probability
        self.priority = priority
        self.num_of_items = num_of_items
        self.category = category

    def __repr__(self):
        return "[" + self.category + ", " + str(self.num_of_items) + ", " + str(self.priority) + ", " + str(self.buy_probability) + "]"


class MatrixEventHandler:
    def person_was_born(self, person):
        pass

    def went_to_shop(self, person, sim_datetime, visit_id):
        pass

    def shopping(self, person, sim_datetime, bought_products, visit_id):
        pass

    def person_died(self, person):
        pass


one_to_one = "ONE_TO_ONE"
one_to_many = "ONE_TO_MANY"


class BaseAssociation:
    def __init__(self, product_category_a, product_category_b):
        if len(product_category_a.strip()) == 0:
            raise ValidationError.field_error("association.category_a", product_category_a)

        if len(product_category_b.strip()) == 0:
            raise ValidationError.field_error("association.category_b", product_category_b)

        self.product_category_b = product_category_b
        self.product_category_a = product_category_a


class ShoppingStageAssociation(BaseAssociation):
    def __init__(self, product_category_a, product_category_b, relation, buy_probability):
        super().__init__(product_category_a, product_category_b)

        if buy_probability < 0.0 or buy_probability > 1.0:
            raise ValidationError.field_error("association.buy_probability", buy_probability)

        is_not_one_to_one = relation.strip() != one_to_one
        is_not_many_to_many = relation.strip() != one_to_many

        if is_not_one_to_one and is_not_many_to_many:
            raise ValidationError.field_error("association.relation", relation)

        self.buy_probability = buy_probability
        self.relation = relation.strip()


class StrongAssociation(ShoppingStageAssociation):
    def __init__(self, product_category_a, product_category_b, relation, buy_probability):
        super().__init__(product_category_a, product_category_b, relation, buy_probability)

    def __repr__(self):
        return "StrongAssociation[" + self.product_category_a + "=>" + self.product_category_b + ", relation: " + self.relation + ", buy probability: " + str(self.buy_probability) + "]"


class Association(ShoppingStageAssociation):
    def __init__(self, product_category_a, product_category_b, relation, buy_probability):
        super().__init__(product_category_a, product_category_b, relation, buy_probability)

    def __repr__(self):
        return "Association[" + self.product_category_a + "=>" + self.product_category_b + ", relation: " + self.relation + ", buy probability: " + str(self.buy_probability) + "]"


class LooselyCoupledAssociation(BaseAssociation):
    def __init__(self, product_category_a, product_category_b, need_probability, buy_probability):
        super().__init__(product_category_a, product_category_b)

        if buy_probability < 0.0 or buy_probability > 1.0:
            raise ValidationError.field_error("association.buy_probability", buy_probability)

        if need_probability < 0.0 or need_probability > 1.0:
            raise ValidationError.field_error("association.need_probability", need_probability)

        self.buy_probability = buy_probability
        self.need_probability = need_probability

    def __repr__(self):
        return "LooselyCoupledAssociation[" + self.product_category_a + "=>" + self.product_category_b + ", need_probability: " + str(self.need_probability) + ", buy probability: " + str(self.buy_probability)



class SimulationProgressEventHandler:
    def on_start(self):
        pass

    def on_end(self):
        pass

    def on_progress_change(self, persons_done, all_people):
        pass
