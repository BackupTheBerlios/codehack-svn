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

"""Team GTK+ GUI"""

from os.path import join
import gtk
import gobject
import time

from codehack import paths
from codehack.gwidget import GWidget, autoconnect_signals_in_class
from codehack import util
from codehack import validators
from codehack.client import dbedit, gui


READY = 'Ready'

class AdminGUI(gui.ClientGUI):
    
    GLADE_FILE = join(paths.DATA_DIR, 'glade', 'admin.glade')
    TOPLEVEL_WIDGET = 'wind_main'

    LBL_CONTEST_INFO = "<big><b>Contest is %srunning</b></big>"
    
    def __init__(self, perspective, userid, disconnect):
        super(AdminGUI, self).__init__(perspective, 'Admin', userid, disconnect)
        self._create_gui()
        self._initialize()
        
    def _create_gui(self):
        # Accounts
        wid = dbedit.DBEdit('users', self.call_remote, 'userid', 
                            lambda x: x['type'] == 'admin')
        wid.add_column('userid', str(), 'Userid', True)
        wid.add_column('passwd', str(), 'Password')
        wid.add_column('name', str(), 'Name', True)
        wid.add_column('emailid', str(), 'Email', True)
        wid.add_column('type', ('team', 'judge'), 'Type', True)
        wid.create(['type', 'userid', 'name', 'emailid'])
        self['vbox_accounts'].pack_start(wid)
        self.db_users = wid

    def show(self):
        self.widget.show()
        self.db_users.show_all()

    def _initialize(self):
        # Get list of accounts
        self.db_users.populate()
        # Get contest time, duration ...
        def done(result):
            duration, age = result
            self._update_contest_ui(duration, age)
        self.call_remote('Getting contest information', done, 
                         'get_contest_info')

    def contest_stopped(self):
        "Called by mind on stop of contest"
        self._update_contest_ui(None, 0)
        
    def _update_contest_ui(self, duration, age):
        """Updates UI based on contest info, duration is None if contest
        is not running"""
        if duration:
            self.contest_time(time.time()-age, duration)
        else:
            self.contest_time(0, None)
        self['lbl_contest'].set_markup(
                self.LBL_CONTEST_INFO % (not duration and 'NOT ' or ''))
        ent = self['ent_duration']
        but_start = self['but_start_contest']
        but_stop = self['but_stop_contest']
        if duration:
            ent.set_text(str(duration))
        else:
            ent.set_text('')
        ent.set_sensitive(not duration)
        but_start.set_sensitive(not duration)
        but_stop.set_sensitive(not not duration)

        
    def on_but_start_contest__clicked(self, but, *args):
        duration = self['ent_duration'].get_text()
        try:
            duration = int(duration)
            if duration < 0:
                raise ValueError
        except ValueError:
            util.msg_dialog('Enter duration in seconds', gtk.MESSAGE_ERROR)
            self['ent_duration'].set_text('')
            return
        def done(result):
            duration, age = result
            # Start time
            self._update_contest_ui(duration, age)
        self.call_remote('Starting contest', done, 'start_contest', duration)

    def on_but_stop_contest__clicked(self, but, *args):
        def done(result):
            self._update_contest_ui(None, 0)
        self.call_remote('Stopping contest', done, 'stop_contest')

    def on_but_logout__clicked(self, *args):
        self.on_quit()
        print 'Hey, don\'t forget to come back!'
