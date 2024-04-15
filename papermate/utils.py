import ads
import ads.libraries

import datetime
from collections import UserDict


__all__ = ['prev', 'BidirectionalCycler',
           'get_user_libraries', 'create_default_library',
           'Cache', 'DateCache']


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


def get_user_libraries():
    q = ads.base.BaseQuery()
    base_url = ads.libraries.Library._libraries_url

    response = q.session.get(base_url).json()['libraries']

    return {d['name']: d['id'] for d in response}


def create_default_library(*, name="papermate", desc="papermate library"):
    try:
        lib = ads.libraries.Library.new(name=name, description=desc,
                                        public=False, docs=[])
    except KeyError as err:
        mssg = f"Default library {name} already exists"
        raise ValueError(mssg) from err

    return {name: lib.id}


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
