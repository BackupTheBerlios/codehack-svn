#!/usr/bin/env python
# Copyright (C) 2004 Sridhar .R <sridhar@users.berlios.de>.
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

"""Contest Profile"""

# This is currently the only way to configure codehack to 
# contest server
#
# First set the 'contest_name' variable to the contest name which was
# used to create the contest (through ./codehack.py --newcontest).
#
# Second, implement the getProfileObject method which must return the 
# profile object.  See codehack/server/profile for notes how to write a profile
# A sample profile (sample.py) is provided for convinience.  sample profile
# follows ACM ICPC rules.

import sys
from os.path import abspath, join
import shutil

TEST_DIR = abspath('test')
TST_JUDGE_DIR = abspath(join(TEST_DIR, 'icpc', 'judge'))

# Set the Contest name here
# It will be used when starting the server through twistd (startserver.tac)
contest_name = 'icpc'

# This function should return the Contest Profile instance
# Write your code here
# 
# IMPORTANT: After first creating a contest, you may want to configure
# it by hand before starting the server
# For example, for SimpleCP profile, .in and .out files must be copied to
# /judge sub-directory in contest directory
# Sample .in and .out files are available in /test/judge
def getProfileObject():
    "Return the Contest Profile instance"
    from codehack.server.profile import samples
    # We remove team's temporary files
    try:
        shutil.rmtree(join(TEST_DIR, contest_name, 'team'))
    except OSError:
        pass
    # The list of problem names
    problems = [
        'Simple addition',
        'Game tree',
        'Derangements',
        'Network Flow'
    ]   
    # List of language definitions (name=>(compile, execute, list_of_ext))
    languages = {
        'C': ("PATH='/usr/bin/' gcc %(inpath)s -o %(in)s -lm", 
            './%(in)s', ['c']),
        'C++': ("PATH='/usr/bin/' g++-3.3 %(inpath)s -o %(in)s -lm", 
            './%(in)s', ['cc', 'cxx', 'c++', 'cpp']),
        'Python': (None, 'python %(inpath)s', ['py']),
        'Java': ('javac %(inpath)s', 'java %(in)s', ['java']),
    }
    # ICPC Score penalty
    score_penalty = 20
    # ACM ICPC Style contest profile
    cp = samples.SimpleCP(TST_JUDGE_DIR, problems, 
                    languages, score_penalty)
    return cp
    
