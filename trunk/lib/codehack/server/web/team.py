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
Team Web Mind
"""

from nevow import tags as T


class NevowTeamMind(object):
    
    def __init__(self, mind, avatar):
        self.mind  = mind
        self.avatar = avatar
        self.init()

    def init(self):
        # Get Contest details
        result = self.avatar.perspective_getInformation()
        self.isrunning = result['isrunning']
        self.name = result['name']
        d = result['details']
        self.duration = d['duration']
        self.age = d['age']
        self.problems = d['problems']
        self.language = d['languages']
        self.results = d['results']
        self.result_acc_index = d['result_acc_index']
        
    def info(self, msg):
        """Message from server"""
        self.mind.set('info', msg)

    def submissionResult(self, result):
        d = self.avatar.perspective_getSubmissions()
        def _cbGot(submissions):
            s = ''
            for run in submissions:
                ts, pr, lang, res = run
                s = s + '%d Seconds, Problem %d, Lang %s, Result %d -- ' % (ts, pr, lang, res)
            self.mind.set('runs', T.b[s])
        return d.addCallback(_cbGot)

    def contestStopped(self):
        self.mind.sendScript('alert("Stopped");')
        # self.gui.contestStopped()

    def contestStarted(self, name, details):
        s = str(dir(self.mind))
        self.mind.sendScript('alert("Started");')
        self.info(T.i[s])
        # self.gui.contestStarted(name, details)
