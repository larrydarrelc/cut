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

        # calculate the mask
        # TODO split it out
        start = self.status.capture.start
        end = self.status.capture.end
        sx, sy = min(start.x, end.x), min(start.y, end.y)
        width, height = abs(start.x - end.x), abs(start.y - end.y)
        hollow = (sx, sy, width, height)
        rect = (0, 0, self.status.width, self.status.height)

        drawers.draw_hollow_mask(cr, rect, hollow)

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

        self.status.dragging = False

    def on_motion_notify(self, widget, event):
        '''Handle mouse move event.'''
        if self.status.dragging:
            # track mouse's trace
            end = self.status.capture.end
            end.x, end.y = utils.get_coordinate_from_event(event)

            self.window.queue_draw()
