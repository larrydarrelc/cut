#coding: utf-8

import gtk
import pygtk
pygtk.require('2.0')
import gtk.gdk as gdk
import gtk.keysyms as keys


def get_keyname_from_event(key_event):
    '''Get key event's name from an event.'''

    def get_modifiers(event):
        modifiers = []

        if not event.state:
            return modifiers

        if gdk.CONTROL_MASK:
            modifiers.append('C')  # ctrl
        if gdk.MOD1_MASK:
            modifiers.append('M')  # alt
        if gdk.SHIFT_MASK and not gdk.keyval_is_upper(event.keyval):
            modifiers.append('S')  # shift but not in uppercase

        return modifiers

    def get_key_name(event):
        key_val = event.keyval
        key_unicode = gdk.keyval_to_unicode(key_val)
        if key_unicode:
            return str(unichr(key_unicode))
        return gdk.keyval_name(key_val)

    if key_event.is_modifier:
        return ''

    keys = get_modifiers(key_event)
    keys.append(get_key_name(key_event))
    
    return '-'.join(keys)


def get_coordinate_from_event(event):
    '''Get (x, y) coordinate from an event.'''

    x, y = event.get_root_coords()
    return int(x), int(y)


class AttrDict(dict):
    '''Attribute accessable dict.'''

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_dict(source, deep=True):
        '''Convert a `:class:dict` instance into a `:class:AttrDict` instance.

        :param source: source `:class:dict` instance
        :param deep: convert `:class:dict` subitems into `:class:AttrDict`
                     instances, default is `True`
        '''
        converted = AttrDict()
        for k, v in source.items():
            if isinstance(v, dict) and not isinstance(v, AttrDict) and deep:
                converted[k] = AttrDict.from_dict(v, deep)
            else:
                converted[k] = v
        return converted
