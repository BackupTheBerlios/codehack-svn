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
import msg
import error


class NevowTeamMind(NevowMind):

    def __init__(self, mind, avatar):
        NevowMind.__init__(self, mind, avatar, TeamPage)

    def init(self):
        # Get submissions
        self.submissions = []
        result = self.avatar.perspective_getInformation()
        self.update_details(result['isrunning'], result['name'],
                            result['details'])
        NevowMind.init(self)
        return self.update_submissions()

    def update_details(self, isrunning, name, details=None):
        "Update new contest details"
        self.isrunning = isrunning
        self.name = name
        if details is not None:
            self.duration = details['duration']
            self.age = details['age']
            self.problems = details['problems']
            self.languages = details['languages']
            self.results = details['results']
            self.result_acc_index = details['result_acc_index']

    def update_submissions(self):
        "Update submissions from database"
        self.submissions = None
        d = self.avatar.perspective_getSubmissions()
        def _cbGot(submissions):
            self.submissions = submissions
        return d.addCallback(_cbGot)

        
    def submitProgram(self, filename, filecontent):
        if not self.isrunning:
            raise error.ContestNotRunning, 'You cannot submit your programs'

        IFE = error.InvalidFilename
        if not '.' in filename:
            raise IFE, "Filename must have an extension"
        splits = filename.split('.')
        if len(splits) != 2:
            raise IFE, "Filename must have single 'dot'"
        progname, ext = filename.split('.')
        try:
            no = int(progname[1:])
        except ValueError:
            raise IFE, "Problem number must be specified"
        if no < 0 or no>=len(self.problems):
            raise IFE, "Problem number is not in range"
        for lang, extensions in self.languages.items():
            if ext in extensions:
                break
        else:
            raise IFE, "Unsupported extension"
        # no, lang
        status = self.avatar.perspective_submitProblem(no, filecontent, lang)
        if status is None:
            raise error.WebServiceError, "Some internal error has occurred. Your problem was not submitted successfully!"
    
    # Mind methods
    #
        
    def info(self, msg):
        """Message from server"""
        # self.mind.set('info', msg)

    def submissionResult(self, result):
        def _cbUpdated(result):
            self.page.status.info(
                "Run result - %d" % len(self.submissions))
            self.js.reload()
        self.update_submissions().addCallback(_cbUpdated)

    def contestStopped(self):
        self.update_details(False, self.name)
        NevowMind.contestStopped(self)

    def contestStarted(self, name, details):
        self.update_details(True, name, details)
        NevowMind.contestStarted(self, name, details)



SUBMIT = 'submit'

class TeamPage(page.MainPage):

    userPage = loaders.xmlfile(join(paths.WEB_DIR, 'team.html'))

    def __init__(self,mind):
        self.mind = mind
        self.avatar = mind.avatar
        super(TeamPage, self).__init__()

    def locateChild(self, ctx, segments):

        if segments[0] == SUBMIT:
            # User has submitted program
            fields = inevow.IRequest(ctx).fields
            # TODO: check the filesize before getting
            # XXX: otherwise this is a major DOS vulnerability!!
            filecontent = fields.getvalue('source')
            filename = fields['source'].filename
            try:
                status = self.mind.submitProgram(filename, filecontent)
            except error.WebServiceError, err:
                self.status.error(err.getMessage())
            else:
                self.status.info('Program submitted successfully')
            return url.URL.fromRequest(inevow.IRequest(ctx)), ()
        
        return super(TeamPage, self).locateChild(ctx, segments)

    def render_submit_button(self, ctx, data):
        if not self.mind.isrunning:
            return ctx.tag(disabled="True")
        return ctx.tag

    def data_runs(self, context, data):
        data = []
        index = 1
        for run in self.mind.submissions:
            ts, pr, lang, res = run
            dct = {}
            dct['run'] = index
            dct['problem'] = pr
            dct['language'] = lang
            dct['result'] = self.mind.results[res]
            dct['ts'] = ts
            data.append(dct)
            index = index + 1
        data.reverse()         # most recent runs first
        return data
        
    def render_run_row(self, context, data):
        for key, value in data.items():
            context.fillSlots(key, value)
        return context.tag
 
    def render_submitProblemForm(self, ctx, data):
        return ctx.tag(
            action=url.here.child(SUBMIT), method="post",
            enctype="multipart/form-data")


