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

"""Judge Avatar"""

from twisted.spread import pb

from codehack.util import log


class JudgeAvatar(pb.Avatar):

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
        log.debug('JudgeAvatar created - %s' % id)
        self.mind = None # see self.ready()
        self.whoami = 'judge'
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
        self.waiting_runs = 0 # number of waiting runs

    def ready(self, mind):
        """Called when avatar is ready for operation.  Until this
        avatar should wait for anything.

        This method is guaranteed to be called *immediately* after
        creating the Avatar object"""
        self.mind = mind
        if self.contest.isrunning():
            self.contestStarted()
            
    def logout(self):
        """Called when this avatar logouts"""

    def connectionAge(self):
        "Return the duration in seconds when avatar is logged in"
        return int(time.time()-self.loginat)
        
# -------------------------------------------------------------------------- #
#   1. getInformation:                          dict
# -------------------------------------------------------------------------- #

    def perspective_getInformation(self):
        """Return dict of isrunning, name, details.
        
        Contest is not running of isrunning is False
        If contest is running, details will be a dict of
        (duration, age)
        """
        isrunning = self.contest.isrunning()
        return {
            'isrunning': isrunning,
            'name': self.contest.name,
            'details': self._contestDetails()
        }
        
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
        
# -------------------------------------------------------------------------- #

    def _contestDetails(self):
        """Return the details dict.
        Note: Contest need not be started
        """
        age = -1
        if self.contest.isrunning():
            age = self.contest.getContestAge()
        details = {
            'duration': self.contest.duration,
            'age': age,
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

    def waiting(self):
        return self.waiting_runs
        
    def getSubmittionResult(self, problem, language, filename):
        """Called when new submission is pending
        
        Return (defer) the submission result"""
        filecontent = file(filename).read()
        # Ask the judge client for evaluation
        # of course, the primary server (this) cannot trust user submitted
        # programs, so this is the job of judge client which could either
        # automate the evaluation process or use a human judge.  In any case
        # the result is deferred.
        self.waiting_runs = self.waiting_runs + 1
        d = self.mind.submissionMade(problem, language, filename, filecontent)
        self.waiting_runs = self.waiting_runs - 1
        return d
