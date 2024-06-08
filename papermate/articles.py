import logging
import pathlib
import textwrap as tw

DEFAULT_DW_DEST = pathlib.Path('~/Downloads').expanduser()

ADS_URL = "ui.adsabs.harvard.edu"


class Article:
    '''representation of an article, based on an ads.search.Article'''

    def __init__(self, entry):

        self._entry = entry

        # bibliographic info
        self.title = entry.title[0]
        self._authors = entry.author
        self.first_author = self._authors[0]
        self.year = entry.year

        # identifiers
        self.bibcode = entry.bibcode
        self._doi = entry.doi if entry.doi is not None else []
        self.bibstem = entry.bibstem[0]
        self.bibgroup = entry.bibgroup

        self._identifiers = entry.identifier

        try:
            self.arxiv_id = [id_ for id_ in self._identifiers
                             if id_.startswith('arXiv:')][0]
        except IndexError:
            self.arxiv_id = None

        # extra frontmatter
        self.abstract = entry.abstract or "No abstract"
        self._affiliations = entry.aff
        self.keywords = entry.keyword

        # analytics
        self._page = entry.page
        self.read_count = str(entry.read_count)
        self.date = entry.pubdate

    @property
    def id(self):
        return f'{self.first_author.split(",")[0]}{self.year}_{self.bibcode}'

    @property
    def authors(self):
        return '; '.join(self._authors)

    @property
    def affiliations(self):
        if all([aff == '-' for aff in self._affiliations]):
            out = "No affiliations found"
        else:
            out = '; '.join([f'({i}) {aff}' for i, aff in
                             enumerate(self._affiliations)])
        return out

    @property
    def doi(self):
        return '; '.join(self._doi)

    @property
    def page(self):
        return '; '.join(self._page)

    @property
    def url(self):
        return f'https://{ADS_URL}/abs/{self.bibcode}'

    @property
    def pdf_url(self):
        # TODO also optionally support trying "/PUB_PDF" maybe
        return f'https://{ADS_URL}/link_gateway/{self.bibcode}/EPRINT_PDF'

    @property
    def arxiv_url(self):
        if self.arxiv_id is not None:
            id_ = self.arxiv_id.split(':')[-1]
            return f'https://arxiv.org/abs/{id_}'

        else:
            mssg = 'No arXiv ID could be found, cannot construct URL'
            raise RuntimeError(mssg)

    def short_authors(self, width):
        '''return a string of authors to fit within the width
        if full list fits, use that, otherwise use et al.
        '''

        authors = tw.wrap(self.authors, width)

        if len(authors) > 1:
            return self.first_author.split(',')[0] + ' et al.'

        else:
            return authors[0]

    def short_abstract(self, width, *, Nchars=300, end='...'):

        short_abs = tw.shorten(self.abstract, Nchars, placeholder=end)

        wrap_abs = tw.wrap(short_abs, width)

        return wrap_abs

    def wrap_property(self, prop, Nchars, *, label=False):
        '''wrap the output of a given property to Nchars'''

        attr = getattr(self, prop)

        if not label:
            wrap_prop = tw.wrap(attr, Nchars)

            return wrap_prop

        else:

            logging.info(f'wrapping with label: {prop=} {Nchars=}, {attr=}')

            lbl = f'{prop} = '
            wrap_prop = tw.wrap(attr, Nchars - len(lbl))

            wrap_prop = [f'{lbl if i == 0 else (" " * len(lbl))} {p}'
                         for i, p in enumerate(wrap_prop)]

            return wrap_prop

    def download(self, dest=DEFAULT_DW_DEST):
        import requests

        pdf_data = requests.get(self.pdf_url)

        with open(f'{dest}/{self.id}.pdf', 'wb') as dest_file:
            dest_file.write(pdf_data.content)

    def open_online(self, *, source='ADS'):
        import webbrowser as wb

        if source.lower() == 'ads':
            wb.open(self.url)

        elif source.lower() == 'arxiv':
            wb.open(self.arxiv_url)

        else:
            raise ValueError(f"Unrecognized source '{source}'")

    def add_to_library(self, *, name='papermate'):

        library_map = get_user_libraries()

        if name not in library_map:
            library_map |= create_default_library()

        id_ = library_map[name]

        lib = ads.libraries.Library(id_)

        resp = lib.add_documents(self.bibcode)

        if resp == 0:
            mssg = "Could not add this article to library. May already exist."
            raise ValueError(mssg)

        return resp
