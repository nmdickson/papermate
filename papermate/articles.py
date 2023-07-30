import pathlib

DEFAULT_DW_DEST = pathlib.Path('~/Downloads').expanduser()


class Article:
    '''representation of an article, based on an ads.search.Article'''

    def __init__(self, entry):

        self._entry = entry

        self.title = entry.title[0]
        self.authors = entry.author
        self.first_author = self.authors[0]
        self.bibcode = entry.bibcode
        self.year = entry.year
        self.abstract = entry.abstract
        self.doi = entry.doi
        self.page = entry.page

        # TODO get links to ads, arxiv, direct pdf

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

    def download(self, dest=DEFAULT_DW_DEST):
        import urllib.request
        # TODO why did I use urlib and not requests?

        pdf_data = urllib.request.urlopen(self.pdf_url)

        with open(f'{dest}/{self.id}.pdf', 'wb') as dest_file:
            dest_file.write(pdf_data.read())

    def open_online(self):
        import webbrowser as wb
        wb.open(self.abs_url)
