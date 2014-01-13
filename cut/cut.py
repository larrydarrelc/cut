#coding: utf-8

import gobject
import gtk
import pygtk
pygtk.require('2.0')

import signals
import utils
from components import RootWindow, FileChooser


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

        # register events
        handlers = (
            ('destroy', self.on_destroy),
            ('expose-event', self.on_expose),
            ('button-press-event', self.on_button_press),
            ('button-release-event', self.on_button_release),
            ('motion-notify-event', self.on_motion_notify),
            ('key-press-event', self.on_key_press)
        )
        for name, handler in handlers:
            self.root.window.connect(name, handler)

        # register custom signals
        handlers = (
            ('screenshot-save', self.on_save_screenshot),
            ('screenshot-copy', self.on_copy_screenshot),
            ('screenshot-discard', self.on_destroy)
        )
        for name, handler in handlers:
            signals.register(name, handler)

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

    def save_to_clipboard(self, pixbuf):
        '''Save screenshot to clipboard.

        :param pixbuf: a `:class:gtk.gdk.Pixbuf` drawable instance
        '''
        clipboard = gtk.clipboard_get()
        clipboard.set_image(pixbuf)
        clipboard.store()

    def save_to_file(self, pixbuf, dest):
        '''Save screenshot to file.

        :param pixbuf: a `:class:gtk.gdk.Pixbuf` drawable instance
        :param dest: save path
        '''
        pixbuf.save(dest, 'png')

    def capture(self):
        '''Capture selected region.'''
        return self.root.desktop.capture(*self.root.captured)

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
        # let root window handle this event
        self.root.on_button_release(widget, event)

    def on_motion_notify(self, widget, event):
        '''Handle mouse button move event.'''
        self.root.on_motion_notify(widget, event)

    def on_copy_screenshot(self, event, widget):
        captured = self.capture()
        self.save_to_clipboard(captured)
        self.root.undraw()

        # FIXME quick fix to make the copied data persistable
        # ref: https://wiki.ubuntu.com/ClipboardPersistence
        gobject.timeout_add_seconds(15, self.on_destroy, widget, event)

    def on_save_screenshot(self, event, widget):
        captured = self.capture()
        self.root.undraw()

        filechooser = FileChooser()
        filechooser.setup(self.root)
        dest = filechooser.draw()
        if dest:
            self.save_to_file(captured, dest)
        self.on_destroy(widget, event)
