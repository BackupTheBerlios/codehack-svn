#!/usr/bin/env python
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

"""Test script to bootstrap"""

import sys
from os.path import abspath, join
import shutil

# Code is kept in lib/
sys.path.insert(0, abspath('lib'))

# We import paths here, to initialize the PATH variables 
# before the CWD is changed by some other part of code
# see: constants.py in lib/
from codehack import paths

TEST_DIR = abspath('test')

TST_JUDGE_DIR = abspath(join('test', 'icpc', 'judge'))

# server
def do_s():
    from codehack.server.profile import samples
    from codehack.server import contest
    try:
        shutil.rmtree(join(TEST_DIR, sys.argv[2], 'team'))
    except OSError:
        pass
    cnt = contest.Contest(sys.argv[2], TEST_DIR)
    cnt.open()
    problems = [
        'Simple addition',
        'Game tree',
        'Derangements',
        'Network Flow'
    ]   
    languages = {
        'C': ("PATH='/usr/bin/' gcc %(inpath)s -o %(in)s -lm", 
            './%(in)s', ['c']),
        'C++': ("PATH='/usr/bin/' g++-3.3 %(inpath)s -o %(in)s -lm", 
            './%(in)s', ['cc', 'cxx', 'c++', 'cpp']),
        'Python': (None, 'python %(inpath)s', ['py']),
        'Java': ('javac %(inpath)s', 'java %(in)s', ['java']),
    }
    score_penalty = 20
    cp = samples.SimpleCP(TST_JUDGE_DIR, problems, 
                    languages, score_penalty)
    cnt.start_server(cp)
    
# client
def do_c():
    from codehack import client
    client.run()
    
# create contest (and repositories, ...)
def do_newcontest():
    contest_name = sys.argv[2]
    from codehack.server import contest
    from getpass import getpass
    cnt = contest.Contest(contest_name, TEST_DIR)
    print 'IMPORTANT: "admin" is the identity for the Admin account'
    apass = None
    while 1:
        apass = getpass("admin's password: ")
        apass2 = getpass("Re-enter password: ")
        if apass == apass2:
            break
        print "Passwords doesn't match"
    aemaild = raw_input("admin's email: ")
    cnt.create(apass, aemaild)
    print contest_name, 'created in', TEST_DIR
    print 'Run "./run.py s %s" to start the server' % contest_name
    

locals()['do_'+sys.argv[1]]()
