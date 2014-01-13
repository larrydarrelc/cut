#coding: utf-8

import gtk
import pygtk
pygtk.require('2.0')

from copy import copy

import drawers
import utils
import signals


def make_button(label, hint, events=None):
    '''Button factory.

    :param label: button label name
    :param hint: button hint
    :param events: connected events, in `(event_name, event_handler)` form
    '''

    # show tooltip
    def on_enter_notify(widget, event):
        widget.set_has_tooltip(True)
        widget.set_tooltip_text(hint)
        widget.trigger_tooltip_query()

        return False

    events = events or []

    button = gtk.Button()
    button.set_label(label)
    button.connect('enter-notify-event', on_enter_notify)

    for name, handler in events:
        button.connect(name, handler)

    return button


class _Component(object):
    '''A component abstract class.

    All subclass must implement the `:meth:setup` method,
    which will initialize the component.

    All subclass must implement the `:meth:draw` method,
    which is used to draw component.

    Each instance must expose a `:class:gtk.Window` window
    attribute.
    '''

    def __init__(self):
        self.window = None

    def setup(self):
        '''Setup component.'''
        raise NotImplementedError('Method setup must be overridden.')

    def draw(self):
        '''Draw component.'''
        raise NotImplementedError('Method draw must be overridden.')


class RootWindow(_Component):
    '''Root window.

    ..attributes:
        window: Instance of `:class:gtk.Window`
        desktop: Drawable pixbuf of current desktop
        status: Window status
    '''

    def setup(self):
        self.status = utils.AttrDict.from_dict({
            # window (desktop) size
            'width': 0,
            'height': 0,
            'dragging': False,
            # capture region
            'capture': {
                'start': {'x': 0, 'y': 0},
                'end': {'x': 0, 'y': 0}
            }
        })

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.fullscreen()
        self.window.set_keep_above(True)

        # get desktop's size
        root = gtk.gdk.get_default_root_window()
        self.status.width, self.status.height = root.get_size()

        # capture current desktop
        self.desktop = Desktop()
        self.desktop.setup(root)

        # setup toolbar
        self.toolbar = Toolbar()
        self.toolbar.setup(self)

    def draw(self):
        self.window.show_all()

    def undraw(self):
        self.toolbar.undraw()
        self.window.hide_all()

    @property
    def captured(self):
        '''Calculate captured rectangle.'''
        start = self.status.capture.start
        end = self.status.capture.end
        sx, sy = min(start.x, end.x), min(start.y, end.y)
        width, height = abs(start.x - end.x), abs(start.y - end.y)
        return (sx, sy, width, height)

    @property
    def background(self):
        '''Calculate background rectangle.'''
        return (0, 0, self.status.width, self.status.height)

    def on_expose(self, widget, event):
        '''Handle the `expose` event.'''
        cr = self.window.window.cairo_create()

        # draw captured desktop
        self.desktop.draw(cr)

        # draw a transparent mask
        if self.status.dragging:
            drawers.draw_hollow_mask(cr, self.background, self.captured)

    def on_button_press(self, widget, event):
        '''Handle mouse press event.'''
        self.status.dragging = True

        # get first drag point
        capture = self.status.capture.start
        capture.x, capture.y = utils.get_coordinate_from_event(event)

    def on_button_release(self, widget, event):
        '''Handle mouse release event.'''

        if self.status.dragging:
            end = self.status.capture.end
            end.x, end.y = utils.get_coordinate_from_event(event)

            self.toolbar.draw()

        self.status.dragging = False

    def on_motion_notify(self, widget, event):
        '''Handle mouse move event.'''
        if self.status.dragging:
            # track mouse's trace
            end = self.status.capture.end
            end.x, end.y = utils.get_coordinate_from_event(event)

            self.window.queue_draw()


class Desktop(object):
    '''Captured desktop.'''

    def setup(self, window):
        '''Capture the desktop.

        :param window: a `:class:gtk.Window` instance
        '''
        self.window, self.colormap = window, window.get_colormap()
        w, h = self.window.get_size()
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        self.pixbuf = pixbuf.get_from_drawable(self.window, self.colormap,
                                               0, 0, 0, 0, w, h)

    def draw(self, cr):
        '''Draw captured desktop.

        :param cr: a `:class:cairo` instance
        '''
        drawers.draw_pixbuf(cr, self.pixbuf)

    def capture(self, x, y, width, height):
        '''Capture a rectangle region pixbuf.

        :param x, y: rectangle start position
        :param width, height: rectangle's size
        '''
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                width, height)
        return pixbuf.get_from_drawable(self.window, self.colormap,
                                        x, y, 0, 0, width, height)


class Toolbar(_Component):
    '''Capture toolbar.

    ..attributes:
        window: Instance of `:class:gtk.Window`
    '''

    def setup_buttons(self):
        '''Setup toolbar buttons.'''
        status = self.status
        toolbox = self.toolbox = gtk.HBox(False, 2)
        container = self.container = gtk.Alignment()
        container.add(toolbox)
        self.window.add(container)

        # setup layout
        container.set(0.5, 0.5, 0, 0)
        container.set_padding(status.padding.y + 2, status.padding.y,
                              status.padding.x, status.padding.x)

        # pack buttons
        builtin_events = []
        buttons = {
            'Save': {
                'hint': 'Save screenshot to file',
                'handler': self.on_save_clicked
            },
            'Copy': {
                'hint': 'Copy screenshot to clipboard',
                'handler': self.on_copy_clicked
            },
            'Discard': {
                'hint': 'Discard change',
                'handler': self.on_discard_clicked
            }
        }
        for name, settings in buttons.items():
            handler = settings.get('handler')
            events = builtin_events
            if handler:
                events = copy(builtin_events)
                # connect to button press event
                events.append(('button-press-event', handler))
            button = make_button(name, settings.get('hint', name), events)
            toolbox.pack_end(button)

    def setup(self, parent):
        '''Setup toolbar.

        :param parent: parent component, a `:class:~_Component` instance
        '''
        status = self.status = utils.AttrDict.from_dict({
            'x': 0, 'y': 0, 'width': 40, 'height': 24,
            'icon': {'width': 28, 'height': 28, 'num': 10},
            'padding': {'x': 5, 'y': 2},
            'offset': {'x': 0, 'y': 5}
        }, deep=True)

        self.parent = parent

        # use `WINDOW_POPUP` to ignore wm's policy`
        window = self.window = gtk.Window(gtk.WINDOW_POPUP)
        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        window.set_keep_above(True)
        window.set_decorated(False)
        window.set_resizable(False)
        window.set_transient_for(self.parent.window)
        window.set_default_size(self.status.width, self.status.height)
        window.set_size_request(
            status.icon.width * status.icon.num + status.padding.x * 2,
            status.icon.height + status.padding.y * 2
        )

        self.setup_buttons()

    def draw(self):
        self.window.show_all()

        # Adjust toolbar's position.
        status = self.status
        tx, ty, tw, th, td = self.window.window.get_geometry()
        rx, ry, rw, rh = self.parent.captured
        bx, by, bw, bh = self.parent.background

        status.width, status.height = tw, th

        if ry + rh + status.offset.y < by + bh - th:  # under region
            status.y = ry + rh + status.offset.y
        elif ry - status.offset.y - th > by:  # on the top
            status.y = ry - status.offset.y - th

        status.x = rx + rw - status.offset.x - tw

        self.window.move(status.x, status.y)

    def undraw(self):
        self.window.hide_all()

    def on_save_clicked(self, widget, event):
        signals.emit('screenshot-save', widget)

    def on_copy_clicked(self, widget, event):
        signals.emit('screenshot-copy', widget)

    def on_discard_clicked(self, widget, event):
        signals.emit('screenshot-discard', widget)


class FileChooser(_Component):
    '''A file chooser dialog.'''

    def setup(self, parent):
        '''Setup file chooser.

        :param parent: parent component a `:class:~_Component` instance
        '''
        window = gtk.FileChooserDialog('Save screenshot to..', parent.window,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        window.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        window.set_default_response(gtk.RESPONSE_ACCEPT)
        window.set_position(gtk.WIN_POS_MOUSE)
        window.set_local_only(True)
        window.set_current_folder('.')
        window.set_current_name('*.png')
        self.window = window

    def draw(self):
        '''Run dialog.'''
        resp = self.window.run()
        name = None
        if resp == gtk.RESPONSE_ACCEPT:
            name = self.window.get_filename()
        self.undraw()
        return name

    def undraw(self):
        '''Destroy dialog.'''
        self.window.destroy()
