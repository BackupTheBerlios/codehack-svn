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

"""Common utilities"""

import logging

from twisted.spread import pb
from twisted.python import log

# TODO: change all references to log.info to log.msg
#       and then remove this hack
log.info = log.msg


APP_NAME = 'codehack'

# Create logger
if 0:
    # We use twisted's log (twistd)
    # so this one is not needed
    log = logging.getLogger(APP_NAME)
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter(">> %(levelname)s %(message)s")
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)

def reverse_dict(dct):
    """Reverse the dictionary"""
    items = dct.items()
    items = map(list, items)
    map(list.reverse, items)
    return dict(items)
    
# Widget parenting
__parent = None

def set_default_parent(widget):
    """Set default parent widget, which is used for
    subsequent calls to GTK+"""
    global __parent
    __parent = widget
    
def get_default_parent():
    """Return the default parent window"""
    return __parent

def msg_dialog(msg, typ=None, buttons=None, parent=None):
    import gtk
    if buttons is None:
        buttons = gtk.BUTTONS_OK
    if typ is None:
        typ = gtk.MESSAGE_INFO
    if parent is None:
        parent = __parent
    md = gtk.MessageDialog(parent=parent, 
                flags=gtk.DIALOG_MODAL, 
                type=typ, 
                buttons=buttons, message_format=msg)
    response = md.run()
    md.hide()
    md.destroy()
    return response
    

# FIXME: 
# In Twisted, raising pb.Error instance from
# registered callbacks prints to server console.
# So we don't use pb.Error at all.
# We simply return (rather than raise'ing) an dictionary
# with only one key 'error_reason', that uniquely identifies
# what exception would have been

def getError(reason):
    assert reason is not None
    return {
        'error_reason': reason
    }

def getReason(error):
    """error must be a dictionary returned by getError
    
    if not 'error' is not returned by getError, return None
    """
    if type(error) is dict and len(error.keys()) == 1 and \
       error.has_key('error_reason'):
        return error['error_reason']
    return None

#~ class OperationError(pb.Error):
    #~ """Operation failed
    
    #~ This exception is raised by server pb and caught by client"""
