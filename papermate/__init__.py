import curses as cs

import interface


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


def controller(screen):

    self.screen = screen

    self.init_screen()

    while True:

        cmd = screen.getch()

        if cmd in COMMANDS:

            self.command(cmd)

        elif cmd in range(NUM_ARTICLES):
            self.go_to_detailed

        # elif cmd in exit_cmds:
        #     # do quitty stuff 
        #     pass

        else:
            continue


if __name__ == '__main__':
    cs.wrapper(interface.Interface().mainloop)

