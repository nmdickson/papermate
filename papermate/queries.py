import ads
import ads.libraries

import datetime
import itertools

from .articles import Article


__all__ = ['Query', 'QuerySet', 'Library']


second_order_operations = (
    "similar", "reviews", "trending", "useful", "citations"
)


def get_user_libraries():
    q = ads.base.BaseQuery()
    base_url = ads.libraries.Library._libraries_url

    response = q.session.get(base_url).json()['libraries']

    return {d['name']: d['id'] for d in response}


def _gen_q(**search_terms):
    '''If necessary for some reason, format a "q" query string, for `ads`'''
    import re

    q = ""

    for field, value in search_terms.items():

        # Wrap value in quotes if not already in parentheses
        if not re.match(r'\s*\(.*\)\s*', value):
            value = '"{}"'.format(value)

        q += ' {}:{}'.format(field, value)

    return q


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
        return f'{self.name} - {self.arxiv_class}'

    def column_str(self, width=30):
        import textwrap as tw

        if width is None:
            return [self.name, self.arxiv_class]

        else:
            return (tw.wrap(self.name, width)
                    + tw.wrap(self.arxiv_class, width))

    def __init__(self, name, bibstem='arxiv',
                 arxiv_class='astro-ph.*', **search_terms):

        self.name = name

        q = ""

        seconds = []

        for term, val in search_terms.items():

            if term in second_order_operations:
                seconds.append(term)

                if not isinstance(val, dict):
                    mssg = (f"{term} is a (second order) operator, requires "
                            f"subtable with (first order) query.")
                    raise ValueError(mssg)

                q += f" {term}({_gen_q(**val)})"

        for term in seconds:
            del search_terms[term]

        self.arxiv_class = arxiv_class

        self._query_dict = dict(
            q=q,
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
        try:
            import tomllib as toml
        except ImportError:
            import tomli as toml

        with open(config, 'rb') as oconf:
            cfg = toml.load(oconf)

        return cls([Query(name=name, **sec) for name, sec in cfg.items()])

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


class Library(QueryResult):

    _fl = [
        'author', 'title', 'year', 'pubdate',
        'doi', 'bibcode', 'bibstem', 'bibgroup', 'identifier',
        'abstract', 'aff', 'keyword',
        'page', 'read_count'
    ]

    @property
    def name(self):
        return self.query.metadata['name']

    @property
    def description(self):
        return self.query.metadata['description']

    def __init__(self, id_):

        lib = ads.libraries.Library(id_)

        result = lib.get_documents(fl=self._fl)

        result.execute()

        super().__init__(lib, result)
