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

"""Submissions manager"""

# FIXME: This module should not be used
# Instead use the pc2 style of submission
#  submit all runs to all judges
#  let the judge (bot or human) select the runs after which that run
#  disappear from other judges view.

from twisted.internet import reactor
from codehack.util import log

class NoJudgeError(RuntimeError):
    
    """No judge logged in currently!"""
    


class Submission(object):
    
    def __init__(self, team, problem_no, problem_lang, ts, filepath):
        self.team = team
        self.problem_no = problem_no
        self.problem_lang = problem_lang
        self.ts = ts
        self.filepath = filepath
        self.judge = None # The judge to which this submission is assigned
        
    def __eq__(self, o):
        s = self
        return s.team == o.team and s.problem_no == o.problem_no and \
               s.problem_lang == o.problem_lang and s.ts == o.ts
        
    def __str__(self):
        return 'Run by %s: %d/%s/%s at %d' % (self.team.userid,
            self.problem_no, self.problem_lang, self.filepath, self.ts)

class SubmissionManager(object):
    
    """Queues incoming submissions requests, submits then to the judge,
    updates the result, scores and re-submits (perhaps to another judge)
    in case of error"""

    # Time to wait before checking for logged-in judge next time
    NO_JUDGE_WAIT = 10
    
    def __init__(self, contest):
        self.contest = contest
        # submission queue
        
        # register events
        la = contest.liveavatars
        la.registerListener(la.EVT_LOGOUT, self._judgeLogout,
                            lambda a: a.whoami == 'judge')
        la.registerListener(la.EVT_LOGIN, self._judgeLogin,
                            lambda a: a.whoami == 'judge')
        # judge -> list of submissions    
        # 'None' key is used to buffer runs that are not yet submitted
        # to any judge
        self._judge_queue = {None: []}
        # reactor.callLater flag
        self._callLater = False
        
    def _flushRuns(self):
        self._callLater = False
        if len(self._judge_queue[None]) == 0:
            return
        try:
            buffered = self._judge_queue[None][:]
            for run in buffered:
                self._submit(run)
                del self._judge_queue[None][0]
        except NoJudgeError:
            self._runsBuffered()
        
    def _runsBuffered(self):
        if self._callLater:
            return
        self._callLater = True
        reactor.callLater(self.NO_JUDGE_WAIT, self._flushRuns)
    
    def _submit(self, s):
        log.debug(str(s))
        try:
            judge = self._getTheMostIdleJudge()
        except NoJudgeError:
            log.warn('No judge logged in, buffering new runs!!')
            self._judge_queue[None].append(s)
            self._runsBuffered()
        else:
            result = judge.getSubmissionResult(
                s.team.userid, s.problem_no, s.problem_lang, s.filepath)
            queue = self._judge_queue[judge.userid]
            queue.append(s)
            result.addCallback(self._result, s)
            return result
        return None
    
    def submit(self, team, problem_no, problem_lang, ts, filepath):
        """New submission"""
        submission = Submission(team, problem_no, problem_lang, ts, filepath)
        return self._submit(submission)
        
    def _result(self, result, submission):
        """Result for submission"""
        self._judge
        
    def _getTheMostIdleJudge(self):
        """Return the most idle judge avatar"""
        judges = [avatar for avatarId, avatar in self.contest.liveavatars.items() if avatar.whoami == 'judge']
        if len(judges) == 0:
            raise NoJudgeError # no judge logged in!!
        waiting_list = [(j.waiting(),j) for j in judges]
        waiting_list.sort() # sort by number of waiting runs
        return waiting_list[0][1] # return the one with least waiting runs

    def _judgeLogout(self, judge):
        """Called when the judge logouts"""
        name = judge.userid
        log.info('SM: judge %s logouts - re-assigning submissions' % name)
        queue = self._judge_queue[name]
        del self._judge_queue[name]
        for submission in queue:
            # resubmit
            self._submit(submission)
        
    def _judgeLogin(self, judge):
        """Called when the judge logins"""
        log.info('SM: judge %s logins' % judge.userid)
        self._judge_queue[judge.userid] = []
        
