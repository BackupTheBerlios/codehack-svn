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
import time

from twisted.internet import defer, reactor
from twisted.spread import pb
from twisted.python import components

from codehack.util import log
from codehack.server import db


class TeamAvatar(pb.Avatar):

    def __init__(self, mind, contest, loginat, id, userid, emailid,
                 webclient=False):
        """
        @param mind:    Client remote object
        @param contest: The contest object
        @param loginat: Timestamp when logged in
        @param id:      The database row id of this user
        @param Userid:  User id
        @param emailid: emailid of the user
        """
        log.debug('TeamAvatar created - %s' % id)
        self.mind = None # see self.ready()
        self.whoami = 'team'
        self.id = id
        self.loginat = loginat
        self.userid = userid
        self.emailid = emailid
        self.contest = contest
        self.webclient = webclient
        self.profile = contest.profile
        self.dbproxy = contest.dbproxy
        self.notify_defer = None  # whether client is waiting
        self.contest_started = False
        self._last_submitted_ts = -1  # Timestamp of last submitted problem
                                      # Used to avoid duplicate timestamps

    def ready(self, mind):
        """Called when avatar is ready for operation.  Untill this
        avatar should wait for anything.

        This method is guaranteed to be called *immediately* after
        creating the Avatar object"""
        self.mind = mind
        if self.contest.isrunning():
            self.contestStarted()

    def connectionAge(self):
        "Return the duration in seconds when avatar is logged in"
        return int(time.time()-self.loginat)
        
# -------------------------------------------------------------------------- #
#   1. getInformation:                          dict
#   2. getSubmissions:                          list
#   3. changePasswd(newpasswd):                 True/False
#   4. submitProblem(pno,ptext,plang):          True
# -------------------------------------------------------------------------- #

    def perspective_getInformation(self):
        """Return dict of isrunning, name, details.
        
        Contest is not running of isrunning is False
        If contest is running, details will be a dict of
        (duration, age, problems, languages, results, result_acc_index)
        """
        isrunning = self.contest.isrunning()
        return {
            'isrunning': isrunning,
            'name': self.contest.name,
            'details': isrunning and self._contestDetails() or None
        }
        
    def perspective_getSubmissions(self):
        """Return all submissions by user"""
        def _cbGotSubmissions(submissions):
            subs_full = [] # List of (timestamp, problem_no, result)
            for problem_subs in submissions:
                if problem_subs:
                    for prob, lang, ts, result in problem_subs:
                        subs_full.append((ts, prob, lang, result))
            subs_full.sort()
            return subs_full
        defer = self.profile.getSubmissions(self.id)
        defer.addCallback(_cbGotSubmissions)
        return defer

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

    def perspective_changePasswd(self, newpasswd):
        """Change the password"""
        d = self.dbproxy.update_user(self.id, password=newpasswd)
        return d.addCallbacks(lambda _: True, lambda _:False)

    def perspective_submitProblem(self, problem_no, problem_text,
                                         problem_lang):
        """Submit a problem"""
        if not self.contest_started:
            return None
        ts = self.contest.getContestAge()
        # If this submission was in the same second as before ..
        if ts == self._last_submitted_ts:
            ts = ts + 1  # add one second to make timestamps unique!
        self._last_submitted_ts = ts

        log.debug('SUBMIT: %d - %s' % (problem_no, problem_lang) )

        # FIXME: renaming doesn't work for Java programs !!
        filename = 'p%d.%s' % (problem_no, \
                    self.profile.getLanguages()[problem_lang][2][0])
        filepath = self.contest.copyFile(
                self, ts, filename, problem_text)
        workdir = os.path.split(filepath)[0]
        input_dict = {
            'inpath': filepath,
            'in': os.path.splitext(os.path.split(filepath)[1])[0]
        }

        reactor.callLater(0,self.profile.submitMeta,
                          self, input_dict, problem_no, problem_lang,
                          ts, workdir)
        return True
        
# -------------------------------------------------------------------------- #

    def _contestDetails(self):
        "Returns details dict"
        cp = self.contest.profile
        problems = cp.getProblems()
        results = cp.getResults()
        languages_ex = cp.getLanguages()
        languages = {}
        for key, (ign, ign, exts) in languages_ex.items():
            languages[key] = exts
        result_acc_index = cp.getACCResult()
        details = {
            'duration': self.contest.duration,
            'age': self.contest.getContestAge(),
            'problems': problems,
            'languages': languages,
            'results': results,
            'result_acc_index': result_acc_index
        }
        return details

    def contestStarted(self):
        "Notification on start of contest"
        self.contest_started = True
        # Inform client
        self.mind.contestStarted(self.contest.name,
                             self._contestDetails())

    def contestStopped(self):
        "Notification on stop of contest"
        self.contest_started = False
        # notify client
        self.mind.contestStopped()
