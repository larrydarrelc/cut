#coding: utf-8

import gtk
import pygtk
pygtk.require('2.0')

import drawers
import utils


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
    
    .. attributes:
        window: Instance of :class:`gtk.Window`
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
            'capture': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
        })

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.fullscreen()
        self.window.set_keep_above(True)

        # get desktop's size
        root = gtk.gdk.get_default_root_window()
        w, h = self.status.width, self.status.height = root.get_size()

        # capture current desktop
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        self.desktop = pixbuf.get_from_drawable(root, root.get_colormap(),
                                                0, 0, 0, 0, w, h)

    def draw(self):
        self.window.show_all()

    def undraw(self):
        self.window.hide_all()

    def on_expose(self, widget, event):
        '''Handle the `expose` event.'''
        cr = self.window.window.cairo_create()

        # draw captured desktop
        drawers.draw_pixbuf(cr, self.desktop)

        # draw a transparent mask
        drawers.draw_mask(cr, 0, 0, self.status.width, self.status.height)

    def on_button_press(self, widget, event):
        '''Handle mouse press event.'''
        self.status.dragging = True
        capture = self.status.capture
        capture.x, capture.y = utils.get_coordinate_from_event(event)

    def on_button_release(self, widget, event):
        '''Handle mouse release event.'''

        if self.status.dragging:
            # Calculate the rectangle. Since each edge is
            # parallel to the monitor, so it's easily find
            # out that the start point is the smaller coordinate
            # value of x and y. For example:
            #
            #     (x0, y0)          (x0 + width, y0)
            #       +------------------+
            #       |                  |
            #       |                  |
            #       |                  |
            #       +------------------+
            #     (x0, y0 + height)  (x0 + width, y0 + height)
            capture = self.status.capture
            sx, sy = capture.x, capture.y
            ex, ey = utils.get_coordinate_from_event(event)
            capture.x, capture.y = min(ex, sx), min(ey, sy)
            capture.width, capture.height = abs(ex - sx), abs(ey - sy)

        self.status.dragging = False
