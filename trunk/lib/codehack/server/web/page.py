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
from nevow import rend
from nevow import loaders
from nevow import guard
from nevow import liveevil
from nevow import static
from nevow import tags as T

from codehack.server import auth
from codehack.server import db

from codehack import paths
      
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

js_timer = """
// timestamps
var ts_start
var ts_end
var ts_enabled = 0

function time_message(msg){
    document.getElementById('progress').innerHTML = msg
}

function time_start(age, total){
    var date = new Date()
    ts_cur = parseInt(date.getTime()/1000)
    ts_start = ts_cur - age
    ts_end = ts_start + total
    ts_enabled = 1
    setTimeout("time_update()", 1000);
}

function time_update(){
    if (!ts_enabled) return
    var date = new Date()
    var ts_current = parseInt(date.getTime()/1000)
    var string = ""
   /* alert(ts_total)
    alert(ts_current)*/
    if (ts_current > ts_end){
        string = "Contest time (" + (ts_end - ts_start) + ") is over"
        return
    }else
        string = (ts_current-ts_start) + "/" + (ts_end-ts_start) + " seconds"
    /*alert("going:" + string)*/
    time_message(string)
    setTimeout("time_update()", 1000)
}

function time_stop(){
    ts_enabled = 0
    time_message('Contest is not running')
}

if (%(timer_enable)s){
   time_start(%(age)s, %(total)s)
}else{
   time_stop()
}
"""

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


    def render_loginname(self, ctx, data):
        return self.avatar.userid

    # Meta Info
    #

    def timer_params(self):
        age = None
        duration = None
        isrunning = self.mind.isrunning
        if isrunning:
            age = self.avatar.contest.getContestAge()
            duration = self.mind.duration
        return isrunning, duration, age

    def render_js_timer(self, ctx, data):
        isrunning, duration, age = self.timer_params()
        js_code = js_timer % {
            'timer_enable': isrunning and 1 or 0,
            'age': age,
            'total': duration
            }
        return T.inlineJS(js_code)
    
    def render_name(self, ctx, data):
        return self.mind.name

    def render_duration(self, ctx, data):
        return self.mind.duration

    def render_status(self, ctx, data):
        return self.status


    def render_logout(self, ctx, data):
        return ctx.tag(href=guard.LOGOUT_AVATAR)

    def render_glue(self, ctx, data):
        return liveevil.glue
  
    def logout(self):
        print 'Bye'


