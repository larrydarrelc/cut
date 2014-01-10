#coding: utf-8

import cairo


def draw_pixbuf(cr, pixbuf, x=None, y=None):
    '''Draw a pixbuf in (x, y).

    :param cr: a `:class:cairo` instance
    :param pixbuf: a `:class:gtk.gdk.Pixbuf` instance that will be drawed
    :param x, y: draw start position, default is (0, 0)
    '''
    x, y = x or 0, y or 0

    cr.set_source_pixbuf(pixbuf, x, y)
    cr.paint()


def draw_mask(cr, x, y, width, height, color=None):
    '''Draw a rectangle mask.
    
    :param cr: a `:class:cairo` instance
    :param x, y: rectangle start position
    :param width, height: rectangle mask's size
    :param color: mask's color in (r, g, b, a) mode, default is (0, 0, 0, 0.5)
    '''
    # ensure it's in (r, g, b, a) mode
    if not isinstance(color, (tuple, list)) or len(color) != 4:
        color = (0, 0, 0, 0.5)

    cr.set_source_rgba(*color)
    # quick fix for large mask
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.rectangle(x, y, x + width, y + height)
    cr.fill()


def draw_hollow_mask(cr, parent, hollow, color=None):
    '''Draw a rectangle mask with a hollow.

    e.g.,:

        +----------------------------------+
        |           top                    |
        |                                  |
        |         +--------+               |
        |  left   |        |               |
        |         |        |     right     |
        |         +--------+               |
        |                                  |
        |            bottom                |
        +----------------------------------+

    :param cr: a `:class:cairo` instance
    :param parent: parent rectangle setting, in (x, y, width, height) form
    :param hollow: hollow rectangle setting, in (x, y, width, height) form
    :param color: mask's color in (r, g, b, a) mode, default is (0, 0, 0, 0.5)
    '''
    # ensure it's in (r, g, b, a) mode
    if not isinstance(color, (tuple, list)) or len(color) != 4:
        color = (0, 0, 0, 0.5)

    rx, ry, rw, rh = parent
    hx, hy, hw, hh = hollow

    # adjust hollow's size & position
    hx, hy = min(rx + rw, hx), min(ry + rh, hy)
    hw, hh = min(rw, hw), min(rh, hh)

    draw_mask(cr, rx, ry, rw, hy, color)  # top
    draw_mask(cr, rx, hy + hh, rw, rh - hy - hh, color)  # bottom
    # FIXME
    # when drawing some small size rectangle,
    # the real size will become larger
    draw_mask(cr, rx, hy, hx, hh, color)  # left
    draw_mask(cr, hx + hw, hy, rw - hx - hw, hh, color)  # right
