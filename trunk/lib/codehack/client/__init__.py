# Copyright (C) 2004 R. Sridhar <sridharinfinity AT users DOT sf DOT net>.
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

"""Codehack client"""

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor

from codehack.client.logindialog import LoginDialog
from codehack import paths

def logged_in(perspective, userid, user_type, mind_proxy, disconnect):
    """Callback called after logging in

    @param perspective: The PB perspective
    @param user_type:   One of 'team', 'judge', 'admin'
    @param mind_proxy:  The Mind proxy object that was passed to server
    @param disconnect:  Function to call for disconnecting
    """
    if user_type not in ['team', 'judge', 'admin']:
        raise ValueError, 'Invalid user type sent by server'
    # Import the respective user module
    from_name = 'codehack.client'
    module_name = '%s.%s' % (from_name, user_type)
    mod = __import__(module_name, globals(), locals(), from_name)
    # Defer this UI method
    reactor.callLater(0, mod.run, perspective, mind_proxy, userid, disconnect)

def run():
    # Set default icon
    _set_default_icon()
    
    # Show Login dialog
    l = LoginDialog(logged_in)
    l.widget.show_all()
    l.set_status('Ready')
    reactor.run()
    
def _set_default_icon():
    import gtk
    from gtk import gdk
    import os.path
    def_icon = gdk.pixbuf_new_from_file( 
        os.path.join(paths.DATA_DIR, 'pixmaps', 'mascot.png')
    )
    gtk.window_set_default_icon_list(def_icon)
