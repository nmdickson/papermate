import os
import shutil
import pathlib
import logging
import datetime
from collections import UserDict

try:
    import tomllib as toml
except ImportError:
    import tomli as toml


__all__ = ['CONFIG', 'prev', 'BidirectionalCycler',
           'get_user_libraries', 'create_default_library',
           'Cache', 'DateCache', 'READMARKERS']


# --------------------------------------------------------------------------
# Setup reminder cronjobs
# --------------------------------------------------------------------------


def setup_cronjob(days, hours, cron=None, overwrite=False):
    import crontab

    cron = crontab.CronTab(user=True) if cron is None else cron

    if list(cron.find_command('papermate-remind')):
        if overwrite:
            remove_cronjob(cron=cron, strict=False)
        else:
            mssg = "cronjob (command=papermate-remind) already exists."
            raise RuntimeError(mssg)

    job = cron.new(command=shutil.which('papermate-remind'))

    job.dow.on(*days)
    job.hour.on(*hours)
    job.minute.on(0)

    cron.write()


def remove_cronjob(cron=None, *, strict=False):
    import crontab

    logging.info('Removing current cronjobs')

    cron = crontab.CronTab(user=True) if cron is None else cron

    Nrem = cron.remove_all(command='papermate-remind')

    if strict and Nrem == 0:
        raise RuntimeError("No cronjob (command=papermate-remind) exists.")

    cron.write()

# --------------------------------------------------------------------------
# Application settings
# --------------------------------------------------------------------------


DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".config/papermate.toml"

SETTINGS_DEFAULTS = {
    "skip_weekends": True,
    "default_library": "papermate",
    "download_location": pathlib.Path.home() / "Downloads",
    "log_file": pathlib.Path.home() / ".local/share/pmate.log",
    "show_relative_date": True,
    "show_loading": True,
    "mark_read": True,
    "ads_api_key": None,
    "reminder": False,
    "reminder_times": [["Mon", "Tue", "Wed", "Thu", "Fri"], [9]],
    "invert_colours": False
}


def touch_config(fn):
    try:
        # If file does not exist, create it (x mode fails if exists)
        file = open(fn, 'x')
        os.chmod(fn, 0o640)

    except FileExistsError:
        file = open(fn)

    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find/open file at {fn}")

    file.close()

    return fn


class _Config:

    def __getattr__(self, key):
        try:
            return self.settings[key]
        except KeyError:
            raise AttributeError(f"'{self}' object has no attribute '{key}'")

    def __init__(self, config_path=DEFAULT_CONFIG_PATH):

        config_path = touch_config(config_path)

        with open(config_path, 'rb') as oconf:
            try:
                self.queries = toml.load(oconf)
            except toml.TOMLDecodeError as err:
                raise toml.TOMLDecodeError("Invalid config file") from err

        self.settings = SETTINGS_DEFAULTS | self.queries.pop('Config', {})

        logging.basicConfig(filename=self.settings['log_file'], filemode='w',
                            level=logging.DEBUG)

        if (api_key := self.settings.get('ads_api_key')) is not None:
            os.environ['ADS_API_TOKEN'] = api_key

        if self.settings.get('reminder', False) is not False:

            cron_times = self.settings.get('reminder_times')

            logging.info(f'setting up cronjob with {cron_times=}')

            if len(cron_times) != 2:
                mssg = ("Invalid config field 'reminder', must be False or "
                        "2-array of (0) days of week and (1) hours of day.")
                raise RuntimeError(mssg)

            setup_cronjob(*cron_times, overwrite=True)

        else:
            # If reminder = false, clear any old cronjobs
            remove_cronjob()


CONFIG = _Config()

# --------------------------------------------------------------------------
# Iteration helpers
# --------------------------------------------------------------------------


def prev(iterable):
    return iterable.__prev__()


class BidirectionalCycler:

    def __iter__(self):
        return self

    def __next__(self):
        try:
            out = self._saved[self._ind]
            self._ind += 1

        except IndexError:
            self._ind = 0
            out = self._saved[self._ind]

        return out

    def __prev__(self):

        out = self._saved[self._ind]

        self._ind -= 1

        if self._ind < 0:
            self._ind = self.N

        return out

    def __init__(self, iterable):
        self._saved = list(iterable)  # not best for memory but it's fine
        self._ind, self.N = 0, len(self._saved) - 1


# --------------------------------------------------------------------------
# Library helpers
# --------------------------------------------------------------------------


def get_user_libraries():
    import ads

    q = ads.base.BaseQuery()
    base_url = ads.libraries.Library._libraries_url

    response = q.session.get(base_url).json()['libraries']

    return {d['name']: d['id'] for d in response}


def create_default_library(*, name=CONFIG.default_library,
                           desc="papermate library"):
    from ads import libraries

    try:
        lib = libraries.Library.new(name=name, description=desc,
                                    public=False, docs=[])
    except KeyError as err:
        mssg = f"Default library {name} already exists"
        raise ValueError(mssg) from err

    return {name: lib.id}


# --------------------------------------------------------------------------
# Caching
# --------------------------------------------------------------------------


class Cache(UserDict):

    def _coerce_id(self, id_):
        '''coerce a given id to a consistent string'''
        return f"{id_}"

    def __setitem__(self, key, value):
        super().__setitem__(self._coerce_id(key), value)

    def __getitem__(self, key):
        return super().__getitem__(self._coerce_id(key))

    def __contains__(self, key):
        return super().__contains__(self._coerce_id(key))

    def cache_results(self, id_, results):
        self.__setitem__(id_, results)


class DateCache(Cache):
    '''simple subclass for storing a cache of query results for various dates'''

    def _coerce_id(self, date):
        '''coerce a given date to a string'''
        try:
            return f'{date:%Y-%m-%d}z00:00'
        except ValueError:
            mssg = "Can only cache items with date as key"
            raise ValueError(mssg)

    def cached_dates(self):
        return [datetime.date.fromisoformat(d.strip("z00:00")) for d in self]


class _ReadMarkers:

    def _coerce_date(self, date):
        return f'{date:%Y-%m-%d}z00:00'

    def __contains__(self, date):

        with open(self.filename, 'r') as of:

            return self._coerce_date(date) in (ln.strip() for ln in of)

    def mark(self, date):

        with open(self.filename, 'a') as of:

            of.write(self._coerce_date(date) + '\n')

    def __init__(self, location=CONFIG.download_location):

        self.filename = pathlib.Path(location) / '.papermate_readmarker.txt'

        self.filename.touch(exist_ok=True)


READMARKERS = _ReadMarkers()
