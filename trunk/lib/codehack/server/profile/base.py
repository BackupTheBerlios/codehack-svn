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
Contest Profile base class functionality
"""

import pickle
from twisted.internet import defer, reactor

from codehack.util import log

class AbstractContestProfile(object):

    "Abstract ContestProfile class"

    def __init__(self, scoregens):
        """
        @param scoregens: List of Score generators, see scoregen.py
        """
        self.scoregens = scoregens

        # The Contest object
        self.contest = None

        # We maintain a score cache (userid=>score object)
        self.score_cache = {}
        self.score_cache_touched = True  # If score cache is touched

    def setContest(self, contest):
        self.contest = contest

    def getProblems(self):
        """Return the list of problem names. Index into this list
        serve as the problem number stored in database"""
        
    def getLanguages(self):
        """Return the dictionary of languages info.

        For eg:
            {
                'Java': ('javac %(input)s', 'java %(inputnoext)s',
                          ['java']),
            }

        List of 'standard' keywords in command string substitution:
            1. inpath - Path to source file
            2. in - Name of source file without extension and path
        """

    def getResults(self):
        """Return the list of Result name/desc. Index into this list
        serve as the result number stored in database"""
        
    def submit(self, team, input_dict,
                          problem, language, timestamp, workdir):
        """Handler for submissions.

        team - Team avatar class (see TeamAvatar.__doc__ for more info)
        input_dict - Dict of 'standard' keywords used in cmd string subst.
        problem - Index into problems list
        language - Index into languages list
        timestamp - Timestamp of submission
        workdir - work directory
        
        Return index into result list (or deferred)
        """

    def calculateScore(self, team, submissions):
        """
        team - TeamAvatar object
        submissions - List (problems) of list (submissons) of tuples
                      (timestamp, result)
        """

    def _update_score(self, team, score):
        try:
            oldscore = self.score_cache[team.userid]
        except KeyError:
            pass
        else:
            # If not change in score ..
            if oldscore == score:
                return
        self.score_cache[team.userid] = score
        self.score_cache_touched = True
        return self._gen_score()

    def _gen_score(self):
        if self.score_cache_touched is False:
            return None  # already upto date
        def done(fullstats):
            for scoregen in self.scoregens:
                scoregen.generate(self.contest.dirs['stat'],
                                self.contest.name,
                                    self.score_cache, fullstats)
            #reactor.callLater(self.score_refresh_interval, self._gen_score)
        d = self.contest.getTeamAvatars()
        return d.addCallback(
            lambda teams: self.getSubmissionsFor(teams).addCallback(done))

    # Final implementations
    def submitMeta(self, team, input_dict,
                          problem, language, timestamp, workdir):
        """(Arguments as in self.submit)

        Wrapper for self.submit, will take care of updating the 
        database and callback with score object
        """
        def followon1(result):
            "Add to database"
            sid = {
                'users_id': team.id,
                'problem': problem,
                'language': language,
                'ts': timestamp,
                'result': result,
            }
            log.debug('DB_Add(sub): %s' %  sid)
            df = self.contest.dbproxy.submissions_add(sid)
            df.addCallback(followon2, result, sid)
            return df

        def followon2(ign, result, sid):
            "(Re-)Calculate scores and updates boards"
            subs_defer = self.getSubmissions(team.id)
            def done(score):
                score_object = self.calculateScore(team, score)
                # store in cache for later reference
                df = self._update_score(team, score_object)
                def done1(res):
                    df = self.contest.dbproxy.users_update(
                        team.userid, {'score': pickle.dumps(score_object)})
                    df.addCallback(followon3, result, score_object, sid)
                    return df
                if df:
                    df.addCallback(done1)
                    return df
                else:
                    return done1(None)
                
            subs_defer.addCallback(done)
            return subs_defer
            

        def followon3(dbresult, result, score_object, sid):
            "Return the result and score"
            dct = {}
            for ky in ('problem', 'ts', 'result', 'language'):
                dct[ky] = sid[ky]
            team.mind.callRemote('submissionResult', dct)
            return result

        result = self.submit(team, input_dict, problem, language,
                             timestamp, workdir)
        # self.submit *may* return a Deferred
        #  In future, self.submit's responsbility may be simplified
        if isinstance(result, defer.Deferred):
            result.addCallback(followon1)
            return result
        else:
            return followon1(result)
        

    def getSubmissions(self, team_dbid, fromproblem=None, returnobject=None):
        """Return all submissions of `team`
        
        See self.calculateScore for return object details
        
        fromproblem and returnobject are used for further callbacks,
        it must not be used by the caller"""
        # FIXME: Is this very slow? .. if so, we need a big refactoring
        #   also I call this method as recursive deferreds ;)
        if fromproblem == None:
            fromproblem = 0
            returnobject = []
        # if all problems are processed return
        if fromproblem == len(self.problems):
            sorted = []
            for pr in returnobject:
                if pr:
                    # We sort submissions by `id`
                    # *not* ts (timestamp), as a team 
                    # could submit (programatically) 2 times 
                    # within the same second
                    # In final return, we return the `id`
                    pr.sort()
                    pr = [(prb,lang,ts,res) for id1,prb,lang,ts,res in pr]
                sorted.append(pr)
            return sorted
        df = self.contest.dbproxy.submissions_get_ex(
                            {'users_id': team_dbid,
                             'problem': fromproblem}, multiple=True)
        def proxy(result):
            if result:
                subs = []
                for res in result:
                    subs.append((res['id'], 
                                res['problem'], res['language'],
                                res['ts'], res['result']))
                returnobject.append(subs)
            else:
                returnobject.append(None)
            return self.getSubmissions(team_dbid, fromproblem+1, returnobject)
        df.addCallback(proxy)
        return df

    def getSubmissionsFor(self, users, fullstats=None):
        """Return all submissions of specified users 
        
        users: List of (id, userid)
        Don't use fullstats
        See self.calculateScore for return object details
        """
        if fullstats is None:
            fullstats = {}
        if len(users) == 0:
            return fullstats
        uid, userid = users[0]
        df = self.getSubmissions(uid)
        def done(result, uid, userid):
            fullstats[userid] = result
            return self.getSubmissionsFor(users, fullstats)
        df.addCallback(done, uid, userid)
        users = users[1:]
        return df
