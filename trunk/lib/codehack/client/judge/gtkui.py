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

"""Judge GTK+ GUI"""

import os.path
from os.path import join
import time
import gtk
import gobject

from codehack import paths, util
from codehack.gwidget import GWidget, autoconnect_signals_in_class
from codehack.client import gui

class JudgeGUI(gui.ClientGUI):
    
    GLADE_FILE = join(paths.DATA_DIR, 'glade', 'judge.glade')
    TOPLEVEL_WIDGET = 'wind_main'

    def __init__(self, perspective, userid, disconnect):
        super(JudgeGUI, self).__init__(perspective, 'Judge', userid, disconnect)
        self.userid = userid
        self.info = {} # Contest info
        self._update_ui(False)
        self._initialize()

    def updateInfo(self, name, details):
        "Update self.info from contest details dict"
        self.info['name'] = name
        if details is None:
            for ky in ('duration', 'age'):
                self.info[ky] = None
            return
        _ = details
        self.info['duration'] = _['duration']
        self.info['age'] = _['age']
    
    def contestStarted(self, name, details):
        self.updateInfo(name, details)
        self._update_ui(True, name)
    
    def contestStopped(self):
        "Called by mind on stop of contest"
        self.updateInfo(None, None)
        self._update_ui(False)

    def _update_ui(self, isrunning, name=None):
        "Change widget attributes based on whether contest is running or not"
        if isrunning is False:
            self.contestTime(0, None)
        else:
            self.contestTime(time.time() - self.info['age'], 
                                self.info['duration'])
        info = '<b>%sContest is%s running</b>'
        if isrunning:
            info = info % ('%s: ' % name, '')
            # contest runs ...
        else:
            info = info % ('', ' NOT')
            # contest doesn't run ...
        self['lbl_contest'].set_markup(info)
        self['nb'].set_sensitive(isrunning)

    def _initialize(self):
        def done(result):
            isrunning, name, details = result
            if result['isrunning']:
                self.contestStarted(result['name'], result['details'])
            else:
                self.contestStopped()
            
        self.call_remote('Getting contest information', done, 
                         'getInformation')

    def on_but_logout__clicked(self, *args):
        self.on_quit()
