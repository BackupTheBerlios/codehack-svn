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
    
class NevowMind:

    def __init__(self, mind, avatar, page):
        self.mind = mind
        self.avatar = avatar
        self.page = page(self)  # The page
        self.name = None        # Contest name
        self.isrunning = False

    def init(self):
        pass

    # Mind methods
    #

    def _setStatus(self):
        "Send to browser the status HTML text"
        # Status text
        for key, value in {
            'name':self.name,
            'duration': self.duration,
            'progress': 'Contest is not running'
            }.items():
            self.mind.set(key, value)
        # Enable/disable form elements
        method_call = ['.setAttribute("disabled", "True")',
            '.removeAttribute("disabled")']
        self.mind.sendScript('document.getElementById("submit_button")' + \
                             method_call[int(self.isrunning)])

    def contestStopped(self):
        self._setStatus()
        self.mind.call('time_stop')
        self.mind.alert("Contest Stopped")
     
    def contestStarted(self, name, details):
        self._setStatus()
        isrunning, duration, age = self.page.timer_params()
        self.mind.call('time_start', age, duration)
        self.mind.alert("Contest Started")
