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

from codehack.util import log


class Submission(object):
    
    def __init__(self, team, problem_no, problem_lang, ts, filepath):
        self.team = team
        self.problem_no = problem_no
        self.problem_lang = problem_lang
        self.ts = ts
        self.filepath = filepath
        
    def __str__(self):
        return 'Run by %s: %d/%s/%s at %d' % (team.name,
            self.problem_no, self.problem_lang, self.filepath, self.ts)

class SubmissionManager(object):
    
    """Queues incoming submissions requests, submits then to the judge,
    updates the result, scores and re-submits (perhaps to another judge)
    in case of error"""
    
    def __init__(self, contest):
        self.contest = contest
        # submission queue
        
        # register events
        la = contest.liveavatars
        la.registerListener(la.EVT_LOGOUT, self._judgeLogout,
                            lambda a: a.whoami == 'judge')
        self._judge_queue = {}  # judge -> list of submissions    
    
    def _submit(self, s):
        log.debug(str(s))
        judge = self._getTheMostIdleJudge()
        result = judge.getSubmissionResult(
            s.problem_no, s.problem_lang, s.filepath)
        queue = self._judge_queue[judge.name]
        queue.append(submission)
        result.addCallback(self._result, submission)
        return result
    
    def submit(self, team, problem_no, problem_lang, ts, filepath):
        """New submission"""
        submission = Submission(team, problem_no, problem_lang, ts, filepath)
        return self._submit(submission)
        
    def _result(self, result, submission):
        """Result for submission"""
        pass
        
    def _getTheMostIdleJudge(self):
        """Return the most idle judge avatar"""
        judges = [avatar for avatarId, avatar in self.contest.liveavatars.items() if avatar.whoami == 'judge']
        waiting_list = [(j.waiting(),j) for j in judges]
        waiting_list.sort() # sort by number of waiting runs
        return waiting_list[0][1] # return the one with least waiting runs

    def _judgeLogout(self, judge):
        """Called when the judge logouts"""
        log.info('SM: judge %s logouts - re-assigning submissions' % judge.name)
        queue = self._judge_queue[judge.name]
        del self._judge_queue[judge.name]
        for submission in queue:
            # resubmit
            self._submit(submission)
        
    def _judgeLogin(self, judge):
        """Called when the judge logins"""
        log.info('SM: judge %s logins' % judge.name)
        self._judge_queue[judge.name] = []
        
class SubmissionQueue