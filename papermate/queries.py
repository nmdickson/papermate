import ads
import ads.libraries
import aiohttp

import datetime
import itertools

from .articles import Article
from .utils import _Config, get_token


__all__ = ['Query', 'QuerySet', 'Library']


second_order_operations = (
    "similar", "reviews", "trending", "useful", "citations"
)


_HEADERS = {
    "Authorization": f"Bearer {get_token()}",
    "User-Agent": f"ads-api-client/{ads.__version__}",
    "Content-Type": "application/json",
}


# --------------------------------------------------------------------------
# Modify `ads` under the hood
# --------------------------------------------------------------------------


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


class _Searcher(ads.SearchQuery):

    async def execute(self, session=None):
        """
        Overwrite SearchQuery.execute just to save the response object even if
        there is an error (for better error messages)
        and to support async execution and shared sessions
        """
        import warnings

        # If session is not shared, get new one from scratch
        if session is None:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                resp = await session.get(self.HTTP_ENDPOINT, params=self.query)

        else:
            resp = await session.get(self.HTTP_ENDPOINT, params=self.query)

        try:
            self.response = await _AsyncSolrResponse.load_http_response(resp)

        except ads.exceptions.APIResponseError as err:
            err.response = resp
            raise err

        header = self.response.responseHeader
        recv_rows = int(header.get("params", {}).get("rows"))
        if recv_rows != self.query.get("rows"):
            self._query['rows'] = recv_rows
            warnings.warn("Response rows did not match input rows. "
                          f"Setting this query's rows to {self.query['rows']}")

        self._articles.extend(self.response.articles)
        if self._query.get('start') is not None:
            self._query['start'] += self._query['rows']
        elif self._query.get('cursorMark') is not None:
            self._query['cursorMark'] = self.response.json.get("nextCursorMark")

        self._highlights.update(self.response.json.get("highlighting", {}))


class _AsyncSolrResponse(ads.search.SolrResponse):
    """
    SolrResponse with support for aiohttp response instead of requests
    """

    def __init__(self, resp_text, resp_json):
        """
        De-serialize a json string representing a solr response
        :param http_response: complete json response from solr
        :type http_response: request.response
        """
        # self._raw = await http_response.text()
        self._raw = resp_text
        # self.json = await http_response.json()
        self.json = resp_json
        self._articles = None
        try:
            self.responseHeader = self.json['responseHeader']
            self.params = self.json['responseHeader']['params']
            self.fl = self.params.get('fl', [])
            if isinstance(self.fl, str):
                self.fl = self.fl.split(',')
            self.response = self.json['response']
            self.numFound = self.response['numFound']
            self.docs = self.response['docs']
        except KeyError as e:
            raise ads.search.SolrResponseParseError("{}".format(e))

    @classmethod
    async def load_http_response(cls, http_response):

        if not http_response.ok:
            raise ads.search.APIResponseError(http_response.text)

        raw = await http_response.text()
        json = await http_response.json()

        c = cls(raw, json)
        c.response = http_response

        ads.RateLimits.getRateLimits(cls.__name__).set(c.response.headers)

        return c


# --------------------------------------------------------------------------
# Setup and execute queries
# --------------------------------------------------------------------------


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

    @property
    def column_str(self):
        return f"{self.name}\n{self.arxiv_class}"

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

    async def execute(self, date=None):

        if date is None:
            date = datetime.datetime.today()

        entdate = f'{date:%Y-%m-%d}z00:00'

        result = _Searcher(entdate=entdate, fl=self._fl, **self._query_dict)

        # TODO should use a base_url here and only get/query in execute
        async with aiohttp.ClientSession(headers=_HEADERS) as session:
            await result.execute(session=session)

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
    def from_configfile(cls, config: _Config):
        return cls([Query(name=name, **sec)
                    for name, sec in config.queries.items()])

    def __init__(self, queries):

        self.queries = queries

    async def execute(self, date=None):
        self.results = QuerySetResult(
            [await q.execute(date=date) for q in self.queries]
        )
        return self.results


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
    '''Note that this is based on a query and so is *read-only*
    '''

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
