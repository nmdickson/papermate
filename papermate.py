import curses as cs

import interface


if __name__ == '__main__':
    cs.wrapper(interface.Interface().mainloop)
