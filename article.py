
class Article:

    def __init__(self, entry):
        '''`entry` is single "entries" dict from feedparser response'''

        # id
        self.id = entry.id.split('/')[-1]

        # get author names
        self.authors = [auth.name for auth in entry.authors]

        # put first author in first position
        self.authors.remove(entry.author)
        self.authors.insert(0, entry.author)

        # parse extra links
        for link in entry.links:

            if link.title == 'pdf':
                self.pdf_url = link.href

            if link.title == 'doi':
                self.doi_url = link.href

        # publishing date
        self.pub_date = entry.updated_parsed

        # abstract
        self.abstract = entry.summary.replace('\n', '')

        # title
        self.title = entry.title

    # TODO function name
    def less_write(self, window, x, y):
        '''write to curses screen for small list page

        [#] title, bold
            author, dim, all or et al.

            abstract, 400 chars, wrapped
        '''



    def more_write(self, window, x, y):
        '''write to curses screen for more info page

        title, bold
        author, dim, all

        \t, abstract, 400 chars, wrapped
        '''