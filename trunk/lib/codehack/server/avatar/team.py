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

"""Team Avatar"""

import os
import os.path
import inspect

from twisted.internet import defer, reactor
from twisted.spread import pb
from twisted.python import components

from codehack.util import log
from codehack.server import db


class TeamAvatar(pb.Avatar):

    def __init__(self, mind, contest, id, userid, emailid):
        """
        @param mind:    Client remote object
        @param contest: The contest object
        @param id:      The database row id of this user
        @param Userid:  User id
        @param emailid: emailid of the user
        """
        log.debug('TeamAvatar created - %s' % id)
        self.mind = mind
        self.whoami = 'team'
        self.id = id
        self.userid = userid
        self.emailid = emailid
        self.contest = contest
        self.profile = contest.profile
        self.dbproxy = contest.dbproxy
        self.notify_defer = None  # whether client is waiting
        self.contest_started = False
        if contest.isrunning():
            self.contestStarted()

    def perspective_get_contest_info(self):
        """Returns isrunning, name, details tuple.
        
        Contest is not running of isrunning is False
        If contest is running, details will be a tuple of
        (duration, contestage, problems, languages, results, result_acc_index)
        """
        duration = self.contest.duration
        isrunning = self.contest.isrunning()
        name = self.contest.name
        details = None
        if isrunning:
            details = self._contest_details()
        return isrunning, name, details
        
    def perspective_get_submissions(self):
        """Return all submissions by user"""
        def done(submissions):
            subs_full = [] # List of (timestamp, problem_no, result)
            for problem_subs in submissions:
                if problem_subs:
                    for prob, lang, ts, result in problem_subs:
                        subs_full.append((ts, prob, lang, result))
            subs_full.sort()
            return subs_full
        defer = self.profile.get_submissions(self)
        defer.addCallback(done)
        return defer

    def _contest_details(self):
        "Returns details tuple"
        cp = self.contest.profile
        problems = cp.getProblems()
        results = cp.getResults()
        languages_ex = cp.getLanguages()
        languages = {}
        for key, (ign, ign, exts) in languages_ex.items():
            languages[key] = exts
        result_acc_index = cp.getACCResult()
        details = (self.contest.duration, self.contest.get_contest_age(),
                    problems, results, languages, result_acc_index)
        return details

    def contestStarted(self):
        "Notification on start of contest"
        self.contest_started = True
        # Inform client
        self.mind.callRemote('contest_started', self.contest.name,
                             self._contest_details())

    def contestStopped(self):
        "Notification on stop of contest"
        self.contest_started = False
        # notify client
        self.mind.callRemote('contest_stopped')
        
    def perspective_whoami(self):
        """Return the string representing this avatar,
        which could be one of the following.
        1. team
        2. judge
        3. admin
        """
        return self.whoami
    
    def perspective_echo(self, obj):
        """Test method that echoes back the object"""
        return obj

    def perspective_change_passwd(self, newpasswd):
        """Change the password"""
        d = self.dbproxy.update_user(self.id, password=newpasswd)
        d.addCallbacks(lambda _: True, lambda _:False)
        return d

    def perspective_submit_problem(self, problem_no, problem_text,
                                         problem_lang):
        """Submit a problem"""
        if not self.contest_started:
            return None
        log.debug('SUBMIT: %d - %s' % (problem_no, problem_lang) )
        ts = self.contest.get_contest_age()
        # FIXME: renaming doesn't work for Java programs !!
        filename = 'p%d.%s' % (problem_no, \
                    self.profile.getLanguages()[problem_lang][2][0])
        filepath = self.contest.copy_file(
                self, ts, filename, problem_text)
        workdir = os.path.split(filepath)[0]
        input_dict = {
            'inpath': filepath,
            'in': os.path.splitext(os.path.split(filepath)[1])[0]
        }
        reactor.callLater(0,self.profile.submit_complete,
                          self, input_dict, problem_no, problem_lang,
                          ts, workdir)
        return True

    def perspective_submit_query(self, problem_no, query):
        """Submit a query"""
        if not self.contest_started:
            return None

