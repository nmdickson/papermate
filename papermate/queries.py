import ads

import datetime
import itertools
from collections import UserDict

from .articles import Article


__all__ = ['Query', 'QuerySet']


class Query:
    '''all the things that go into making an ADS query

    we should have a list of them, loaded from a config file
    '''

    _fl = [
        'author', 'title', 'year', 'pubdate',
        'doi', 'bibcode', 'bibstem', 'bibgroup', 'identifier',
        'abstract', 'aff', 'keyword',
        'page', 'read_count'
    ]

    def __str__(self):
        return f'{self.keywords} - {self.arxiv_class}'

    def column_str(self, width=30):
        import textwrap as tw

        if width is None:
            return [self.keywords, self.arxiv_class]

        else:
            return (tw.wrap(self.keywords, width)
                    + tw.wrap(self.arxiv_class, width))

    def __init__(self, keywords, bibstem='arxiv', arxiv_class='astro-ph.*',
                 **search_terms):

        self.keywords = keywords
        self.arxiv_class = arxiv_class

        self._query_dict = dict(
            full=keywords,
            bibstem=bibstem,
            arxiv_class=arxiv_class,
            **search_terms
        )

    def execute(self, date=None):

        if date is None:
            date = datetime.datetime.today()

        entdate = f'{date:%Y-%m-%d}z00:00'

        result = ads.SearchQuery(entdate=entdate, fl=self._fl,
                                 **self._query_dict)

        result.execute()

        return QueryResult(self, result)


class QueryResult:

    def __iter__(self):
        yield from self.articles

    def __init__(self, query, result):

        self.query = query
        self.articles = [Article(a) for a in result]

        self.empty = len(self.articles) == 0

        self.response = result.response


class QuerySet:
    '''a bunch of queries '''

    def __iter__(self):
        yield from self.queries

    def __len__(self):
        return len(self.queries)

    @classmethod
    def from_configfile(cls, config):
        import configparser
        # TODO change config files to toml files and use tomllib when 3.11

        cfg = configparser.ConfigParser()
        cfg.read(config)

        return cls([Query(**cfg[sec]) for sec in cfg.sections()])

    def __init__(self, queries):

        self.queries = queries

    def execute(self, date=None):
        return QuerySetResult([q.execute(date=date) for q in self.queries])


class QuerySetResult:
    '''The results of a QuerySet being executed'''

    def __iter__(self):
        yield from self.results

    def items(self):
        yield from zip(self.queries, self.results)

    def __init__(self, results):

        self.queries = [r.query for r in results]
        self.results = results
        self.articles = list(itertools.chain(*[r.articles for r in results]))


class Cache(UserDict):
    '''simple subclass for storing a cache of query results for various dates'''

    def _coerce_date(self, date):
        '''coerce a given date to a string'''
        try:
            return f'{date:%Y-%m-%d}z00:00'
        except ValueError:
            mssg = "Can only cache items with date as key"
            raise ValueError(mssg)

    def __setitem__(self, key, value):
        super().__setitem__(self._coerce_date(key), value)

    def __getitem__(self, key):
        return super().__getitem__(self._coerce_date(key))

    def __contains__(self, key):
        return super().__contains__(self._coerce_date(key))

    def cached_dates(self):
        return [datetime.date.fromisoformat(d.strip("z00:00")) for d in self]

    def cache_results(self, date, results):
        self.__setitem__(date, results)
