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

"""Codehack main script"""

import setpath
from optparse import OptionParser

import profile

parser = OptionParser()
ao = parser.add_option

ao("-n", "--newcontest", dest="newcontest", metavar="ContestName",
   help="Create new contest")
ao("-c", "--client", action="store_true", default=False,
   help="Run codehack client")

(options, args) = parser.parse_args()

if options.newcontest:
    from codehack.server import contest
    from getpass import getpass
    contest_name = options.newcontest
    cnt = contest.Contest(contest_name, profile.TEST_DIR)
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
    print contest_name, 'created in', profile.TEST_DIR
    print 'Modify profile.py and use "twistd -noy startserver.tac" to start the server'

if options.client:
    from codehack.client.base import run
    run()

