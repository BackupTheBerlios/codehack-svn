/* 
 * Copyright (C) 2004 Sridhar .R <sridhar@users.berlios.de>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software 
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */


/*
 * Utility functions
 */
function getId(id){
    return document.getElementById(id);
}

/*
 * Contest timer
 */
var ts_start;
var ts_end;
var ts_enabled = 0;

function time_message(msg){
    getId('progress').innerHTML = msg;
}

function time_start(age, total){
    var date = new Date();
    ts_cur = parseInt(date.getTime()/1000);
    ts_start = ts_cur - age;
    ts_end = ts_start + total;
    ts_enabled = 1;
    setTimeout("time_update()", 1000);
}

function time_update(){
    if (!ts_enabled) return;
    var date = new Date();
    var ts_current = parseInt(date.getTime()/1000);
    var string = "";
    if (ts_current > ts_end){
        string = "Contest time (" + (ts_end - ts_start) + ") is over";
        return;
    }else
        string = (ts_current-ts_start) + "/" + (ts_end-ts_start) + " seconds";
    time_message(string);
    setTimeout("time_update()", 1000);
}

function time_stop(){
    ts_enabled = 0;
    time_message('Contest is not running');
}


