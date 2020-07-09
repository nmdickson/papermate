class Interface():

    def init_screen(self):

        self.screen.clear()

        # get info about total screen size, for sizing of windows
        self.height, self.width = self.screen.getmaxyx()

    def mainloop(self, screen):

        self.screen = screen

        self.init_screen()

        while True:

            cmd = screen.getch()

            if cmd in COMMANDS:

                self.command(cmd)

            elif cmd in exit_cmds:
                # do quitty stuff
                pass

            else:
                continue

