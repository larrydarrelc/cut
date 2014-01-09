#coding: utf-8

import gtk
import pygtk
pygtk.require('2.0')

import utils
from components import RootWindow


class CutManager(object):
    '''A screenshot helper.
    
    ..attributes:
        root: a `:class:RootWindow` instance, root window
        keybindings: key press event callback pool
    '''

    def _setup_windows(self):
        '''Setup all windows.'''
        self.root = RootWindow()
        self.root.setup()

    def _setup_events(self):
        '''Setup all events.
        
        ..notes:
            All events should be handled by the manager itself.
        '''
        events_mask = (gtk.gdk.KEY_RELEASE_MASK
                       | gtk.gdk.POINTER_MOTION_MASK
                       | gtk.gdk.BUTTON_PRESS_MASK
                       | gtk.gdk.BUTTON_RELEASE_MASK)
        self.root.window.add_events(events_mask)

        handlers = (
            ('destroy', self.on_destroy),
            ('expose-event', self.on_expose),
            ('button-press-event', self.on_button_press),
            ('button-release-event', self.on_button_release),
            ('button-release-event', self.on_destroy),
            ('motion-notify-event', self.on_motion_notify),
            ('key-press-event', self.on_key_press)
        )
        for name, handler in handlers:
            self.root.window.connect(name, handler)

    def _setup_keybindings(self):
        '''Setup keybindings.
        
        ..notes:
            Each callback should register to `key_bindings` with k-v pair.
            Callback function must be a 0 argument callable object.
        '''
        self.key_bindings = dict([
            ('Escape', lambda: self.on_destroy(self.root.window))
        ])

    def __init__(self):
        self._setup_windows()
        self._setup_events()
        self._setup_keybindings()

        self.root.draw()
        gtk.main()

    def save(self, pixbuf):
        '''Save snapshot.

        :param pixbuf: a `:class:gtk.gdk.Pixbuf` drawable instance
        '''
        clipboard = gtk.clipboard_get()
        clipboard.set_image(pixbuf)
        clipboard.store()

    def on_destroy(self, widget, event=None):
        # restore cursor
        self.root.window.window.set_cursor(None)
        gtk.main_quit()

    def on_expose(self, widget, event):
        self.root.on_expose(widget, event)

        # propagate to the children
        children = widget.get_child()
        if children:
            widget.propagate_expose(children, event)

        return True

    def on_key_press(self, widget, event):
        '''Handle key press event.'''
        key = utils.get_keyname_from_event(event)
        if key in self.key_bindings:
            self.key_bindings[key]()

    def on_button_press(self, widget, event):
        '''Handle mouse button press event.'''
        self.root.on_button_press(widget, event)

    def on_button_release(self, widget, event):
        '''Handle mouse button release event.'''
        self.root.on_button_release(widget, event)

        captured = self.root.status.capture
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                captured.width, captured.height)
        region = self.root.window.get_window()
        pixbuf = pixbuf.get_from_drawable(region, region.get_colormap(),
                                          captured.x, captured.y, 0, 0,
                                          captured.width, captured.height)
        self.save(pixbuf)

    def on_motion_notify(self, widget, event):
        '''Handle mouse button move event.'''


if __name__ == '__main__':
    CutManager()