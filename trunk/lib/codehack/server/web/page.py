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
Pages - <Refactor this>
"""

import time
from os.path import join

from twisted.cred import portal
from twisted.cred import checkers
from nevow import rend
from nevow import loaders
from nevow import guard
from nevow import liveevil
from nevow import static
from nevow import tags as T

from codehack.server import auth
from codehack.server import db

from codehack import paths
      
def web_file(*fil):
    return join(paths.WEB_DIR, *fil)


class LoginPage(rend.Page):
    
    "The Login page"
    
    addSlash = True
    docFactory = loaders.xmlfile(web_file('login.html'))

    def render_loginForm(self, ctx, data): 
        return ctx.tag(action=guard.LOGIN_AVATAR, method='POST')

    def logout(self):
        pass


class MainPage(rend.Page):

    "Common Page methods"

    addSlash = True

    # Directories
    cssDirectory = join(paths.WEB_DIR, 'styles')
    jsDirectory = join(paths.WEB_DIR, 'js')

    child_css = static.File(web_file(cssDirectory),
                           defaultType="text/css")
    child_js = static.File(web_file(jsDirectory),
                           defaultType="text/javascript")
    
    # The glue
    render_glue = liveevil.glue
    render_codehack_glue = T.inlineJS(
        file(web_file('js', 'codehack.js')).read())                          

    def render_body(self, ctx, data):
        "On page load call self.mind.pageInit"
        return ctx.tag(onload=liveevil.handler(
            lambda client: self.mind.pageInit()))

    # Meta Info
    #

    def render_status(self, ctx, data):
        return self.status

    def render_logout(self, ctx, data):
        return ctx.tag(href=guard.LOGOUT_AVATAR)

    def logout(self):
        print 'Bye'


