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

import error

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


class StatusNotifier:

    """Convinient class for notifying info/error messages
    to browser that either sent POST/GE request or a liveevil
    callback"""

    DEFAULT = None

    def __init__(self, contest):
        self.contest = contest # contest object (for time, age info)
        self._msg = self.DEFAULT
        self._error = False
        self._messages = []  # List of ts, message, error tuple

    def info(self, info):
        "Information to be displayed in browser"
        self._msg = info
        self._error = False
        self._messages.append([self._getAge(), info, False])

    def error(self, error):
        "Error to be displayed in browser"
        self._msg = error
        self._error = True
        self._messages.append([self._getAge(), error, True])

    def _getAge(self):
        "Return contest age, -1 if contest isn't running"
        if self.contest.isrunning() is False:
            return -1
        return self.contest.getContestAge()

    def _reset(self):
        self._msg = self.DEFAULT
        self._error = False

    def render(self):
        msg, error = self._msg, self._error
        self._reset()
        return msg, error

    def getMessages(self):
        return self._messages


class MainPage(rend.Page):

    "Common Page methods"

    addSlash = True

    # The userpage (loaders.htmlfile)
    # This will be included in the page
    userPage = None

    docFactory = loaders.xmlfile(
        join(paths.WEB_DIR, 'userpage.html'))

    # Directories
    cssDirectory = join(paths.WEB_DIR, 'styles')
    jsDirectory = join(paths.WEB_DIR, 'js')

    child_css = static.File(web_file(cssDirectory),
                           defaultType="text/css")
    child_js = static.File(web_file(jsDirectory),
                           defaultType="text/javascript")
    child_liveevil = liveevil.glueJS
    

    def __init__(self, *args, **kwargs):
        super(MainPage, self).__init__(*args, **kwargs)
        self.status = StatusNotifier(self.mind.avatar.contest)

    def render_glue(self, ctx, data):
        "All in one glue!"
        stans = []
        stans.append(T.script(src="liveevil", language="javascript"))
        stans.append(T.script(src="js/codehack.js", langauge="javascript"))
        js = """
        function onLoad(){
          var isrunning = %(isrunning)s;
          if (isrunning){
             time_start(%(age)s, %(duration)s);
          }else{
             time_stop();
          }
        }
        """
        age = None
        if self.mind.isrunning:
            age = self.mind.avatar.contest.getContestAge()
        info_dict = {
            'isrunning': self.mind.isrunning and 'true' or 'false',
            'age': age,
            'duration': self.mind.duration
        }
        stans.append(T.inlineJS(js % info_dict))
        return stans

    def render_body(self, ctx, data):
        "On page load call self.mind.pageInit"
        #return ctx.tag(onload=liveevil.handler(
        #    lambda client: self.mind.pageInit()))
        return ctx.tag(onload="onLoad();")

    def render_userpage(self, ctx, data):
        return self.userPage

    # Meta Info
    #

    def render_loginname(self, ctx, data):
        return ctx.tag[self.mind.avatar.userid]

    def render_name(self, ctx, data):
        return ctx.tag[self.mind.name]

    def render_duration(self, ctx, data):
        duration = 'Contest is not running'
        if self.mind.isrunning:
            duration = self.mind.duration
        return ctx.tag[duration]

    def render_status(self, ctx, data):
        msg, error = self.status.render()
        if msg is None:
            msg = ''
        return ctx.tag(class_=["info", "error"][error])[msg]

    def data_messages(self, ctx, data):
        data = self.status.getMessages()[:]
        data.reverse()
        return data

    def render_message_row(self, ctx, data):
        ts, msg, error = data
        ctx.tag(class_=["info", "error"][error])
        ctx.fillSlots("msg", msg)
        ctx.fillSlots("ts", ts)
        return ctx.tag
        
    def render_logout(self, ctx, data):
        return ctx.tag(href=guard.LOGOUT_AVATAR)

    def logout(self):
        print 'Bye'


