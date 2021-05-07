import datetime
import calendar

day = datetime.timedelta(days=1)


class Matrix:
    def __init__(self, config):
        self.start_date = datetime.date(config.global_settings.year, config.global_settings.start_month, 1)
        self.last_day_date = datetime.date(
            config.global_settings.year,
            config.global_settings.end_month,
            calendar.monthrange(config.global_settings.year, config.global_settings.end_month)[1]
        )
        self.actual_date = self.start_date

    def run(self):
        while self.actual_date <= self.last_day_date:
            print(self.actual_date.strftime("Actual time: %d %m %y"))
            print("doing something...")
            self.actual_date += day


class Configuration:
    def __init__(self, global_settings):
        self.global_settings = global_settings


class GlobalSettings:
    def __init__(self, start_month, end_month, year):
        self.year = year
        self.end_month = end_month
        self.start_month = start_month





