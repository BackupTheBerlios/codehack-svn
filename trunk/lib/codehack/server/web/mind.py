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

"""
Codehack Nevow Mind
"""

from jsutil import JSUtil


class NevowMind:

    """Mind wrapper for Nevow clients.

    mind - original mind
    avatar - avatar for this mind
    page - The corresponding page *class*

    see: auth.py for mechanism
    """

    def __init__(self, mind, avatar, page):
        self.mind = mind
        self.avatar = avatar
        self.page = page(self)  # The page
        self.name = None        # Contest name
        self.isrunning = False
        self.js = JSUtil(mind)

    def __getattr__(self, attr):
        # Fallback to original mind's attribute
        return getattr(self.mind, attr)

    def init(self):
        "Called when the mind is first created (on user logon)"
        pass

    def pageInit(self):
        "Called when the page is loaded"
        if self.isrunning:
            self._startTimer()
        else:
            self._stopTimer()
        self._sendMeta()
        # Show the page
        js = self.js
        js.visible('loading', False)
        js.visible('mainBody', True)

    def _startTimer(self):
        # Start timer
        age = None
        duration = None
        isrunning = self.isrunning
        if isrunning:
            age = self.avatar.contest.getContestAge()
            duration = self.duration
        self.mind.call('time_start', age, duration)

    def _stopTimer(self):
        self.mind.call('time_stop')

    def _sendMeta(self):
        "Send contest meta-info to browser"
        js = self.js
        # Set nodes
        js.set('loginname', self.avatar.userid)    # Userid
        js.set('name', self.name)                  # Contest name
        js.set('duration', self.duration)          # Duration of contest
        # Enable/disable form elements
        # 'Upload' button
        method_call = ['.setAttribute("disabled", "True")',
            '.removeAttribute("disabled")']
        self.mind.sendScript('document.getElementById("submit_button")' + \
                             method_call[int(self.isrunning)])
        
    # Mind methods
    #

    def contestStopped(self):
        self._sendMeta()
        self._stopTimer()
        self.mind.alert("Contest Stopped")
     
    def contestStarted(self, name, details):
        self._sendMeta()
        self._startTimer()
        self.mind.alert("Contest Started")
