import numpy as np

from textual.app import App, ComposeResult
from textual import widgets
from textual.widget import Widget
from textual.containers import Horizontal, Vertical, Center
from textual.dom import NoScreen
from textual import events, on
from textual.binding import Binding


# HACKY AF WAY TO ADD NEW BORDER< SHOULD MAKE NEW BUTTON WIDGET??
#   or a new button "variant" if thats easier?
import textual._border
import textual.css.constants
textual._border.BORDER_LOCATIONS['angled'] = textual._border.BORDER_LOCATIONS['solid']
textual._border.BORDER_CHARS['angled'] = (('┌', '─', '┐'), ('>', ' ', '<'), ('└', '─', '┘'))
textual.css.constants.VALID_BORDER.add('angled')


class TripleHeader(widgets.Static):
    """A header with left, center, and right-aligned text."""

    def compose(self) -> ComposeResult:
        yield Horizontal(
            widgets.Static(self.version, id='left-align'),
            widgets.Static(self.title, id='centre-align'),
            widgets.Static(self.date, id='right-align'),
        )

    def set_title(self, title: str):
        '''Update the central title'''
        self.title = title
        self.query_one("#centre-align", widgets.Static).update(self.title)

    def __init__(self) -> None:
        super().__init__()
        import datetime
        from .. import __version__

        self.version = f'papermate ({__version__})'

        self.title = ''

        self.date = datetime.datetime.today().strftime('%Y-%m-%d ')


class QRCode(widgets.Static):

    def make_qr(self, content: str, compress: int = 10, version: int = 1, inverse=True) -> str:
        import qrcode
        # TODO making specific size is difficult. right now can play with
        #   version (and compress) but can't really force a width...

        # Make the QR code for this text
        qr = qrcode.make(content, version=version)

        # Get the binary image data (and decrease resolution to make it fit)
        qr_data = np.array(qr)[::compress, ::compress].astype(int)

        # Make sure this is an even shape on the y-axis, for below
        if qr_data.shape[0] % 2 != 0:
            qr_data.resize((qr_data.shape[0] + 1, qr_data.shape[1]))
            qr_data[-1, :] = 1

        # We're using half-line resolution characters, so compress data again
        qr_data = qr_data[::2, :] + (2 * qr_data[1::2, :])

        # Turn the data into unicode chars to match
        chars = np.empty(qr_data.shape, dtype=np.str_)
        char_table = ['█','▄','▀',' '] if inverse else [' ','▀','▄','█']
        chars = np.select(
            [(qr_data == i) for i in range(4)],
            char_table,
            default=''
        )

        # Put data together into single string
        return '\n'.join(''.join(row) for row in chars)

    def __init__(self, content: str, compress: int = 10, version: int = 1, inverse: bool = True):
        self.qr = self.make_qr(content, compress=compress, version=version, inverse=inverse)
        super().__init__(self.qr)

    def on_mount(self):
        self.styles.width = 'auto'


class DateLoadingIndicator(widgets.LoadingIndicator):

    # TODO might be nice to still have splash screen on first time

    def __init__(self, date=None) -> None:
        super().__init__()
        self.date = date

    def render(self):
        from rich.text import Text
        mssg = f"\n{self.date}" or ''
        return Text(f'Loading articles for{mssg}\n\n') + super().render()


class ContentWindow(Widget):
    '''the widget that holds all the actual content, basically everything
    except the header and footer, so the app compose is just
    header | contentwindow | footer'''

    def on_mount(self):
        self.styles.border = ('solid', 'white')
        self.styles.align = ('center', 'middle')

