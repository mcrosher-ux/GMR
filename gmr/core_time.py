#gmr/core_time
from gmr.constants import WEEKS_PER_YEAR


class GameTime:
    def __init__(self, year=1947):
        self.year = year
        self.month = 0
        self.week = 1
        self.absolute_week = 1

    def advance_week(self):
        self.week += 1
        self.absolute_week += 1
        if self.week > 4:
            self.week = 1
            self.month += 1
            if self.month > 11:
                self.month = 0
                self.year += 1


def get_season_week(time):
    """Convert absolute_week into 1..WEEKS_PER_YEAR so the calendar repeats each year."""
    return ((time.absolute_week - 1) % WEEKS_PER_YEAR) + 1
