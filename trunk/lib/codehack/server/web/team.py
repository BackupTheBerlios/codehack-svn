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

from os.path import join

from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow import liveevil
from nevow import inevow
from nevow import guard
from nevow import url
from nevow import static

from codehack import paths

from mind import NevowMind
import page


class StaticItemStore:

    def __init__(self, value):
        self.value = value

    def __getitem__(self, item):
        return self.value

class NevowTeamMind(NevowMind):

    def __init__(self, mind, avatar):
        NevowMind.__init__(self, mind, avatar, TeamPage)

    def init(self):
        NevowMind.init(self)
        # Get submissions
        self.submissions = []
        result = self.avatar.perspective_getInformation()
        self.update_details(result['isrunning'], result['name'],
                            result['details'])
        return self.update_submissions()

    def update_details(self, isrunning, name, details=None):
        "Update new contest details"
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
            stanobj = self.runsHTML()
            self.mind.set('runs', stanobj)
            self.mind.alert('Runs updated')
        return self.update_submissions().addCallback(_cbGot)

    def contestStopped(self):
        self.update_details(False, self.name)
        NevowMind.contestStopped(self)

    def contestStarted(self, name, details):
        self.update_details(True, name, details)
        NevowMind.contestStarted(self, name, details)



SUBMIT = '_submit'

class TeamPage(page.MainPage):

    docFactory = loaders.xmlfile(
        join(paths.WEB_DIR, 'team.html'))


    def __init__(self,mind):
        self.mind = mind
        self.avatar = mind.avatar
        self.status = '' # status messages


    def locateChild(self, ctx, segments):
 
        if segments[0] == SUBMIT:
            # Submit user submitted program
            fields = inevow.IRequest(ctx).fields
            filecontent = fields.getvalue('source')
            filename = fields['source'].filename
            status = self.mind.submitProgram(filename, filecontent)
            if status is True:
                self.status = 'Successfully submitted'
            else:
                self.status = status
            
            return url.URL.fromRequest(inevow.IRequest(ctx)), ()
        return rend.Page.locateChild(self, ctx, segments)

    def render_runs(self, ctx, data):
        return self.mind.runsHTML()
 
    def render_submitProblemForm(self, ctx, data):
        return ctx.tag(
            action=url.here.child(SUBMIT), method="post",
            enctype="multipart/form-data")


