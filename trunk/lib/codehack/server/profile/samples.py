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

"Sample ContestProfile's"


import os.path
from twisted.internet import defer, protocol, error, process

# service is API to codehack for ContestProfile's
from codehack.server import services, profile, scoregen

# ICPC scoring

class ScoreObject(object):
    
    "Score Object for SimpleCP profile"
    
    def __init__(self):
        self.score = 0   # total score
        self.nr_acc = 0  # number of problems solved
        
    def __cmp__(self, anscore):
        # equal no. of problems solved?
        if self.nr_acc == anscore.nr_acc:
            # then compare their scores
            if self.score == anscore.score:
                return 0
            elif self.score > anscore.score:
                return -1
            return 1
        if self.nr_acc > anscore.nr_acc:
            return 1
        return -1

    def __str__(self):
        return 'solved: %d, score: %d' % (self.nr_acc, self.score)


# TODO: Writing CP's must be made easy .. some thoughts
#
#       1. Remove Twisted knowledge
#       2. Provide support for good callback based execution of processes

class SimpleCP(profile.AbstractContestProfile):

    """Simple profile
        
        TODO: brief explanation of what this does

        - submissions: Evaluation based on matching of output with .out file
        - scores: ScoreObject is score, penalty is also supported
                  (scoring will resemble ICPC scoring)

    This profile can be sub-classed for more finer control
    """

    def __init__(self, 
            judge_data_dir, problems, languages,
            score_penalty):
        """
        judge_data_dir - Directory where judge's input/output files live
                         Input files are: p0.in, p1.in ...
                         Output files are: p0.out, p1.out, ...
        problems, languages - To be returned from getProblems, getLanguages
        score_penalty - Penalty points to be added for (previous) 
                        wrong submission
        """
        self.judge_data_dir = judge_data_dir
        self.problems = problems
        self.languages = languages
        self.score_penalty = score_penalty

        # Hard-coded Results list!
        #  because, submit() uses this (static) information for
        #  evaluation
        # If supposed to be passed to __init__, there is no way
        # to tell submit() which is which!
        self.results = [
            'Accepted - Your solution was accepted',
            'Wrong Answer - Your solution produced wrong answer',
            'Compilation Error - Your program was compiled unsuccessfuly',
            'Runtime Error - Your program gave way to runtime error. ' + \
                'Possibly segmentation fault?!',
            'Time limit exceeded - Your program exceeded its limit in ' + \
                'execution time',
            'Memory limit exceeded - Your program occupied more memory'
        ]

        # A solution to above 'Hard-coded Results' problem would be
        #  passing of such indices to __init__, but that is 
        #  unused flexibility IMO.
        self.RES_ACC = 0
        self.RES_WA = 1
        self.RES_CE = 2
        self.RES_RE = 3
        self.RES_TLE = 4
        self.RES_MLE = 5
        # In fact, another solution is to associate a string for each 
        #  of the above index, so I guess this is a better solution of all
        #  but again, this is unused flexibility ;)

        # Resource limits
        #  hmm, you may need to have a look at safeexec.py !
        #  This is list of resource arguments to be passed to safeexec.py
        self.res_limits = [
            "RLIMIT_NOFILE=120,120",
        ]

        # CP needs 1 or more scoregen's
        rgen = scoregen.RankingsGen(20, problems, languages, 
                                    self.results, self.RES_ACC)
        super(SimpleCP, self).__init__([rgen])

    # Okay, now we implement the abstract methods
    #
    
    def getProblems(self):
        return self.problems

    def getLanguages(self):
        return self.languages

    def getResults(self):
        return self.results
        
    def getACCResult(self):
        return self.RES_ACC

    def calculateScore(self, team, submissions):
                    
        score = ScoreObject()
        assert submissions
        for pr in submissions:
            # was the problem ever submitted?
            if pr is None:
                continue
            penalty = 0
            for prob, lang, ts, result in pr:
                if result == self.RES_ACC:
                    score.score = score.score + ts + penalty
                    score.nr_acc = score.nr_acc + 1
                    break # if submissions after ACC are to be discarded!
                # all others must be penalized
                penalty = penalty + self.score_penalty
        return score

    def submit(self, team, input_dict,
                     problem, language, timestamp, workdir):
        # The ungliest part of this method is
        #  whenever a longer operation (such as compile, execution)
        #  is to be done, we need to start it (the operation)
        #  and return from the method, just after passing the follow-on
        #  method as an argument.
        #  On completion of that long operation that follow-on method will
        #  be called.
        #  Also in such case, submit() must return defer.Deferred instance
        #   and the last Followon method will just .callback the result
        #   on this deferred object to simulate the real return
        # What an ugly part.  Probably you can use defgen.py from twisted svn
        # to make this more pretty!

        cmd_compile, cmd_exe = self.languages[language][:2]

        # Save locals() for use in followon's
        #  FIXME: ugly! corrupts self's namespace!!
        #    also "overlapping call" BUG! BUG! BUG!
        self.result_defer = defer.Deferred()
        self.cmd_exe = cmd_exe
        self.input_dict = input_dict
        self.problem = problem
        self.team = team
        self.workdir = workdir
        
        # Compile, if necessary
        if cmd_compile:
            services.safe_system(self._followon_compiled, 
                               cmd_compile % input_dict, 
                               workdir, self.res_limits)
        else:
            self._followon_compiled(0)

        # Followon will take care, just return from method 
        return self.result_defer
            

    # Followon's after submit()
    #  Each followon method will result argument, but don't bother
    def _followon_compiled(self, result):
        # Now the program is compiled
        #  result contains the return code (surprisingly
        
        # Compilation error?
        if result != 0:
            self.result_defer.callback(self.RES_CE)
            return

        # Proceed with execution
        infile = os.path.join(self.judge_data_dir, 'p%d.in' % self.problem)
        outfile = os.path.join(self.judge_data_dir, 'p%d.out' % self.problem)
        # See class Evaluator below
        pp = Evaluator(self, self.result_defer, infile, outfile)
        services.safe_spawn(pp, self.cmd_exe % self.input_dict, 
                          self.workdir, self.res_limits)
        self.result_defer.addCallback(self._followon_executed)
        return self.result_defer

    def _followon_executed(self, result):
        return result


# TODO: Check whether this works
#       Then generalize this as a service in service.py
#       finally hide twisted related API and make our CP API clean
class Evaluator(protocol.ProcessProtocol):
    
    """Evaluator for SimpleCP. Does a straightforward comparison
    of program output with outfile
    """
        
    def __init__(self, sh, defer, infile, outfile):
        """
        cp - ContestProfile object
        infile, outfile - Input and outfile file
        """
        self.sh = sh
        self.input = file(infile, 'r')
        self.output = file(outfile, 'r')
        self.result = None
        self.defer = defer

    def connectionMade(self):
        # Pass the input all at once and close stdin
        self.transport.write(self.input.read())
        self.input.close()
        self.transport.closeStdin()

    def outReceived(self, data):
        # Compare `so-far-received` data
        correct_data = self.output.read(len(data))
        if data != correct_data:
            self.result = self.sh.RES_WA

    def errReceived(self, data):
        # we skip stderr
        pass
        
    def outConnectionLost(self):
        if self.output.read() == '':
            self.result = self.sh.RES_ACC

    def processEnded(self, status):
        # FIXME: complete this
        if isinstance(status.value, error.ProcessDone):
            self.done()
        elif isinstance(status.value, error.ProcessTerminated):
            self.result = self.sh.RES_RE
            self.done()

    def done(self):
        "Kills the process"
        try:
            self.transport.loseConnection()
            self.transport.signalProcess("KILL")
        except process.ProcessExitedAlready:
            pass
        self.defer.callback(self.result)
