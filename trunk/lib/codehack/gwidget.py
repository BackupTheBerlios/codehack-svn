# Copyright (C) 2004 Sridhar .R <sridhar@users.berlios.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""GWidget - Making use of glade files easier."""

import os.path
import sys
import gtk
from gtk import glade
import gobject

from util import msg_dialog


class GWidget(object):
    """Wrapper for glade XML.
    
    A GWidget represents a toplevel widget in a glade file.  Widgets descending
    from that toplevel widget can be accessed using item reference syntax.
    Methods of the form <on/after>_widgetname__signalname are automatically 
    connected with respective signals and widgets.
    
    ``on_quit`` method if defined will be connected to ``delete-event``
    event of the toplevel widget.
    
    @cvar `GLADE_FILE`    : Path of the glade file to use.
    @cvar `TOPLEVEL_WIDGET` : Name of the toplevel widget.
    """

    # Path of glade file
    GLADE_FILE = None
    # Toplevel widget name
    TOPLEVEL_WIDGET = None
    
    # Properties
    gladexml = property(lambda self: self._gladexml, doc='GladeXML object')
    widget = property(lambda self: self._widget, doc='Toplevel widget')
    
    def __init__(self, autoconnect_now=True):
        """
        :Parameters:
            - `autoconnect_now`: If False, doesn't autoconnect signals
        """
        self._gladexml = glade.XML(self.GLADE_FILE, self.TOPLEVEL_WIDGET)
        self._widget = self.gladexml.get_widget(self.TOPLEVEL_WIDGET)
        self._widget.connect('delete-event', self.on_quit)
        self._widgets_cache = {}        # Widgets are stored in cache for
                                        #  quicker future retrieval
        if autoconnect_now:
            self.autoconnect_signals()
    
    def on_quit(self, *args):
        self.widget.hide()
        self.widget.destroy()
    
    def autoconnect_signals(self):
        autoconnect_signals_in_class(self._gladexml.get_widget, self)
        
    def __getitem__(self, item):
        try:
            return self._widgets_cache[item]
        except KeyError:
            widget = self._gladexml.get_widget(item)
            if not widget:
                raise ValueError, 'No such widget [%s] in GladeXML object' % item
            self._widgets_cache[item] = widget
            return widget


def autoconnect_signals_in_class(widget_getter, instance_object):
    """Autoconnect methods in given instance
    
    @param widget_getter:   A callable that returns widget when passed name
    @param instance_object: The instance that holds the methods as handlers
    """
    autoconnect_signals(widget_getter, 
                            instance_object.__class__.__dict__,
                            lambda x: getattr(instance_object, x))

def autoconnect_signals(widget_getter, hdlr_dict, hdlr_getter=None):
    """Autoconnect methods with unique format with widget actions.
    
    @param widget_getter: A callable that returns widget when passed name
    @param hdlr_dict:     A dictionary holding the methods that needs to be
                          autoconnected.  name->method_object
    @param hdlr_getter:   If hdlr_dict has inappropriate values (class for eg.)
                          and if this is non-none, it will be passed the key
                          to get the value.
    """
    ON_PRE = 'on_'
    AFTER_PRE = 'after_'
    conn_func = gobject.GObject.connect
    conn_after_func = gobject.GObject.connect_after
    for key, hdl in hdlr_dict.items():
        if hdlr_getter:
            hdl = hdlr_getter(key)
        if not callable(hdl): continue
        # connect function for on/after callbacks
        connect_func = None
        if key.startswith(ON_PRE):
            connect_func = conn_func
            wid_in = len(ON_PRE)
        elif key.startswith(AFTER_PRE):
            connect_func = conn_after_func
            wid_in = len(AFTER_PRE)
        else:
            continue
        
        # Get widget and signal name
        sig_in = key.rfind('__')
        if sig_in <= wid_in:
            #print >>sys.stderr, 'Unknown callback method %s' % key
            continue
        wid_name = key[wid_in:sig_in]
        sig_name = key[sig_in+2:]
        # Substitue '_' for '-' in signal name
        sig_name.replace('_', '-')
        new_widget = widget_getter(wid_name) or getattr(self, wid_name)
        if new_widget is not None:
            connect_func(new_widget, sig_name, hdl)
        else:
            print >>sys.stderr, 'Handler error for [%s]. No such widget [%s]' % (key, wid_name)


