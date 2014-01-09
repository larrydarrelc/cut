#coding: utf-8


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
    
    :param cr: a `cairo` instance
    :param x, y: rectangle start position
    :param width, height: rectangle mask's size
    :param color: mask's color in (r, g, b, a) mode, default is (0, 0, 0, 0.5)
    '''
    # ensure it's in (r, g, b, a) mode
    if not isinstance(color, (tuple, list)) or len(color) != 4:
        color = (0, 0, 0, 0.5)

    cr.set_source_rgba(*color)
    cr.rectangle(x, y, x + width, y + height)
    cr.fill()
