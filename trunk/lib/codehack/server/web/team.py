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


class StaticItemStore:

    def __init__(self, value):
        self.value = value

    def __getitem__(self, item):
        return self.value

class NevowTeamMind(object):
    
    def __init__(self, mind, avatar):
        self.mind  = mind
        self.avatar = avatar
        self.init()

    def init(self):
        # Get Contest details
        self.submissions = []
        result = self.avatar.perspective_getInformation()
        self.update_details(result['isrunning'], result['name'],
                            result['details'])
        return self.update_submissions()

    def update_details(self, isrunning, name, details=None):
        self.isrunning = isrunning
        self.name = name
        d = details
        if d is None:
            d = StaticItemStore('Contest is not running')
        self.duration = d['duration']
        self.age = d['age']
        self.problems = d['problems']
        self.languages = d['languages']
        self.results = d['results']
        self.result_acc_index = d['result_acc_index']

    def update_submissions(self):
        "Update submissions from database"
        d = self.avatar.perspective_getSubmissions()
        def _cbGot(submissions):
            self.submissions = submissions
        return d.addCallback(_cbGot)

    def submitProgram(self, filename, filecontent):
        if not self.isrunning:
            return 'Contest is not running. You cannot upload file.'
        if not '.' in filename:
            return 'Filename should have an extension'
        splits = filename.split('.')
        if len(splits) != 2:
            return 'Invalid fileame. Cannot contain multiple . character'
        progname, ext = filename.split('.')
        try:
            no = int(progname[1:])
        except ValueError:
            return 'Filename should have problem number'
        if no < 0 or no>=len(self.problems):
            return 'Filename should have problem number in range %d to %d' \
                   % (0, len(self.problems-1))
        for lang, extensions in self.languages.items():
            if ext in extensions:
                break
        else:
            return 'No supported language accepts this file. Check your ' + \
                   'file extension'
        # no, lang
        status = self.avatar.perspective_submitProblem(no, filecontent, lang)
        if status is None:
            return 'Problem in submission. Try again'
        return True

    def runsHTML(self):
        "Return submissions stat as HTML"
        items = []
        for run in self.submissions:
            ts, pr, lang, res = run
            item = T.li[[T.strong[pr], '/', T.i[lang], ': ',
                    T.em[self.results[res]], ' in ', ts, ' seconds']]
            items.append(item)
        items.reverse() # newer run on top!
        return T.ol[items]

    # Mind methods
    #
        
    def info(self, msg):
        """Message from server"""
        self.mind.flt('info', msg)

    def submissionResult(self, result):
        def _cbGot(result):
            # FIXME: this liveevil stuff not working!
            # stanobj = self.runsHTML()
            # self.mind.flt('runs', stanobj)

            # Since the above doesn't work :(, we got for a full
            # page reload!
            # render_ method will take care of displaying the
            # new data
            self.mind.sendScript('window.location.reload()')
        return self.update_submissions().addCallback(_cbGot)

    def contestStopped(self):
        self.update_details(False, self.name)
        self.mind.sendScript('alert("Stopped");')
        # self.gui.contestStopped()

    def contestStarted(self, name, details):
        self.update_details(True, name, details)
        self.mind.sendScript(
            'alert("Started");')
