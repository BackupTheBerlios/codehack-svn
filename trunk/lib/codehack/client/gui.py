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

"""Codehack client - GUI common base class"""

import time

import gtk
import gobject
from twisted.internet import reactor

from codehack.gwidget import GWidget
from codehack import util


READY = 'Ready'

class ClientGUI(GWidget):
    
    """Client GUI window that often call remote methods on server
    freeze/unfreeze UI and callRemote wrapper are provided
    
    Needs widgets: statusbar, progressbar
    """
    
    def __init__(self, perspective, usertype, userid, disconnect):
        """
        @param perspective: The perspective of server
        @param disconnect:  Function for disconnecting
        """
        super(ClientGUI, self).__init__()
        self.disconnect = disconnect
        self.widget.set_title('%s - Codehack %s' % (userid, usertype))
        self.perspective = perspective
        # Status bar
        self._statuscontext = self['statusbar'].get_context_id('Client')
        self.set_status(READY) 
        self.contest_time(0,None)
        self.update_progress()
        
    def on_quit(self, *args):
        self.disconnect()
        gtk.main_quit()
        
    def show(self, *args):
        # Show all, but specific (supposed to be) hidden widgets
        self.widget.show_all()
        
    def set_status(self, msg):
        """Set the statusbar message"""
        self['statusbar'].push(self._statuscontext, msg)

    def contest_time(self, start_timestamp, duration):
        """Set contest start timestamp (needed for progress bar update)"""
        self.__contest_start = start_timestamp
        self.__contest_duration = duration
        
    def update_progress(self):
        """Update progress display"""
        pb = self['progressbar']
        age = time.time() - self.__contest_start
        duration = self.__contest_duration
        if duration is None:
            frac = 0.0
            text = 'not running'
        else:
            if age >= duration:
                age = duration
            frac = float(age)/duration
            text = '%d secs left!' % (duration - age)
        pb.set_fraction(frac)
        pb.set_text(text)
        reactor.callLater(1, self.update_progress)
        
    def freeze(self):
        """Freeze UI so that no UI action gets done"""
        self.widget.set_sensitive(False)
        
    def unfreeze(self):
        """Unfreeze the UI"""
        self.widget.set_sensitive(True)
        
    # Callback for all deferreds
    def _cb_done(self, result, next_success_callback):
        reason = util.getReason(result)
        if reason:
            # Error raised by server
            util.msg_dialog(reason, gtk.MESSAGE_ERROR)
        else:
            # Normal return
            if next_success_callback:
                next_success_callback(result)
        self.unfreeze()
        self.set_status(READY)
    
    # Errback for all deferreds
    def _cb_oops(self, reason):
        msg = reason.getErrorMessage()
        util.msg_dialog('CRITICAL: ' + msg, gtk.MESSAGE_ERROR)
        self.set_status(READY)
        self.unfreeze()
        
    # Wrapper for .callRemote(
    def call_remote_ex(self, desc, done, method, freeze, *args, **kwargs):
        """<Re-usable function>"""
        self.set_status(desc + ' ...')
        if freeze:
            self.freeze()
        d = self.perspective.callRemote(method, *args, **kwargs)
        # We pass the actual success callback 'done' to _cb_done,
        # which will conditionally call it, if not error was returned
        d.addCallback(self._cb_done, done)
        d.addErrback(self._cb_oops)
        
    def call_remote(self, desc, done, method, *args, **kwargs):
        self.call_remote_ex(desc, done, method, True, *args, **kwargs)
        
    def call_remote_sync(self, desc, done, method, *args, **kwargs):
        self.call_remote_ex(desc, done, method, False, *args, **kwargs)

    def callLater(self, func, *args, **kwargs):
        reactor.callLater(0, func, *args, **kwargs)
