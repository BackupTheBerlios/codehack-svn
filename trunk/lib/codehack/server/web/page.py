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
Nevow Test - REMOVE or rename later
"""

import time
from os.path import join

from twisted.cred import portal
from twisted.cred import checkers

from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow import liveevil
from nevow import inevow
from nevow import guard
from nevow import url

from codehack import paths
from codehack.server import auth
from codehack.server import db


      
def web_file(fil):
    return join(paths.WEB_DIR, fil)

class LoginPage(rend.Page):
    
    "The Login page"
    
    addSlash = True
    docFactory = loaders.xmlfile(web_file('login.html'))

    def render_loginForm(self, ctx, data): 
        return ctx.tag(action=guard.LOGIN_AVATAR, method='POST')

    def logout(self):
        pass

SUBMIT = '_submit'

class MainPage(rend.Page):

    addSlash = True
    docFactory = loaders.xmlfile(web_file('main.html'))

    def __init__(self,mind):
        self.mind = mind
        self.avatar = mind.avatar

    def locateChild(self, ctx, segments):
 
        if segments[0] == SUBMIT:
            fields = inevow.IRequest(ctx).fields
            filecontent = fields.getvalue('source')
            self.mind.info('<b>File:</b>' + filecontent + fields['source'].filename)
            d = self.avatar.perspective_submitProblem(0, filecontent, 'Python')
            # Redirect away from the POST
            return url.URL.fromRequest(inevow.IRequest(ctx)), ()
        return rend.Page.locateChild(self, ctx, segments)

    def render_loginname(self, ctx, data):
        return self.avatar.userid

    # Meta Info
    #
    
    def render_name(self, ctx, data):
        return self.mind.name

    def render_age(self, ctx, data):
        return self.mind.age

    def render_duration(self, ctx, data):
        return self.mind.duration
        
    def render_status(self, ctx, data):
        i = self.avatar.perspective_getInformation()
        if not i['isrunning']:
            return T.b['Contest is NOT running']
        name = i['name']
        i = i['details']
        # duration, age, problems, languages, results, result_acc_index
        html = T.p[T.h3['Problems'], T.i[str(i['problems'])], \
                T.h3['Duration'], T.i[str(i['duration'])]]
        return html
        
    def render_submitProblemForm(self, ctx, data):
        return ctx.tag(action=url.here.child(SUBMIT), method="post", enctype="multipart/form-data")
                    
    def render_logout(self, ctx, data):
        return ctx.tag(href=guard.LOGOUT_AVATAR)

    def render_glue(self, ctx, data):
        return liveevil.glue
    
    def fun(self):
        self.mind.sendScript('alert("Good boy!");')
        from twisted.internet import reactor
        reactor.callLater(3, self.fun)
    
    def logout(self):
        print 'Bye'
