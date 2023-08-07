import pathlib

DEFAULT_DW_DEST = pathlib.Path('~/Downloads').expanduser()

ADS_URL = "ui.adsabs.harvard.edu"


class Article:
    '''representation of an article, based on an ads.search.Article'''

    def __init__(self, entry):

        self._entry = entry

        # bibliographic info
        self.title = entry.title[0]
        self.authors = entry.author
        self.first_author = self.authors[0]
        self.year = entry.year

        # identifiers
        self.bibcode = entry.bibcode
        self.doi = entry.doi
        self.bibstem = entry.bibstem[0]
        self.bibgroup = entry.bibgroup

        self._identifiers = entry.identifier

        try:
            self.arxiv_id = [id_ for id_ in self._identifier
                             if id_.startswith('arXiv:')][0]
        except IndexError:
            self.arxiv_id = None

        # extra frontmatter
        self.abstract = entry.abstract
        self.affiliations = entry.aff
        self.keywords = entry.keyword

        # analytics
        self.page = entry.page
        self.read_count = self.read_count

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
        import textwrap as tw

        auth_str = '; '.join(self.authors)

        authors = tw.wrap(auth_str, width)

        if len(authors) > 1:
            return self.first_author.split(',')[0] + ' et al.'

        else:
            return authors[0]

    def short_abstract(self, width, *, Nchars=300, end='...'):
        import textwrap as tw

        short_abs = tw.shorten(self.abstract, Nchars, placeholder=end)

        wrap_abs = tw.wrap(short_abs, width)

        return wrap_abs

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
