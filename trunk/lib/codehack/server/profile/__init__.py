# Copyright (C) 2004 R. Sridhar <sridharinfinity AT users DOT sf DOT net>.
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

"""Contest Profile

A profile is a class that has contest specific code that 

    1. Evaluates submitted programs
    2. Maintains score object
    3. Renders (the same) score object

WARNING: API is not yet freezed, it may change in future.
"""

import pickle
from twisted.internet import defer, reactor


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

    def set_contest(self, contest):
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
                print '**scoregen:', self.score_cache, fullstats
                scoregen.generate(self.contest.dirs['stat'],
                                self.contest.name,
                                    self.score_cache, fullstats)
            #reactor.callLater(self.score_refresh_interval, self._gen_score)
        df = self._get_all_submissions()
        df.addCallback(done)
        return df

    # Final implementations
    def submit_complete(self, team, input_dict,
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
            df = self.contest.dbproxy.submissions_add(sid)
            df.addCallback(followon2, result, sid)
            return df

        def followon2(ign, result, sid):
            "(Re-)Calculate scores and updates boards"
            subs_defer = self.get_submissions(team)
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
            team.mind.callRemote('submission_result', 
                            sid['problem'], sid['language'],
                            sid['ts'], sid['result'])
            return result

        result = self.submit(team, input_dict, problem, language,
                             timestamp, workdir)
        # self.submit *may* return a Deferred
        #  In future, self.submit's responsbility may be simplified
        if isinstance(result, defer.Deferred):
            result.addCallback(followon1)
            return result
        else:
            return followon(result)
        

    def get_submissions(self, team, fromproblem=None, returnobject=None):
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
                    pr = [(prb,lang,ts,res) for id,prb,lang,ts,res in pr]
                sorted.append(pr)
            return sorted
        df = self.contest.dbproxy.submissions_get_ex(
                            {'users_id': team.id,
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
            return self.get_submissions(team, fromproblem+1, returnobject)
        df.addCallback(proxy)
        return df

    def _get_all_submissions(self, users=None, fullstats=None):
        """Return all submissions of all teams
        
        Don't use users and fullstats
        See self.calculateScore for return object details
        """
        print '***get', users, fullstats
        if users is None:
            fullstats = {}
            print '**avatars', self.contest.avatars
            users = self.contest.avatars.keys()
        if len(users) == 0:
            return fullstats
        df = self.get_submissions(self.contest.avatars[users[0]])
        def done(result, user):
            fullstats[user] = result
            return self._get_all_submissions(users, fullstats)
        df.addCallback(done, users[0])
        users = users[1:]
        return df
