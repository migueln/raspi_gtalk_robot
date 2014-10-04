﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

# PyGtalkRobot: A simple jabber/xmpp bot framework using Regular Expression Pattern as command controller
# Copyright (c) 2008 Demiao Lin <ldmiao@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Homepage: http://code.google.com/p/pygtalkrobot/
#

import sys, traceback
import xmpp
import urllib
import re
import inspect

"""A simple jabber/xmpp bot framework

This is a simple jabber/xmpp bot framework using Regular Expression Pattern as command controller.
Copyright (c) 2008 Demiao Lin <ldmiao@gmail.com>

To use, subclass the "GtalkRobot" class and implement "command_NUM_" methods
(or whatever you set the command_prefix to), like sampleRobot.py.

"""

def print_info(obj):
    for (name, value) in inspect.getmembers(obj):
        print '%s: %r' % (name, value)

class GtalkRobot:

    ########################################################################################################################
    conn = None
    show = "available"
    status = "PyGtalkRobot"
    commands = None
    command_prefix = 'command_'
    GO_TO_NEXT_COMMAND = 'go_to_next'
    ########################################################################################################################
    
    #Pattern Tips:
    # I or IGNORECASE <=> (?i)      case insensitive matching
    # L or LOCALE <=> (?L)          make \w, \W, \b, \B dependent on the current locale
    # M or MULTILINE <=> (?m)       matches every new line and not only start/end of the whole string
    # S or DOTALL <=> (?s)          '.' matches ALL chars, including newline
    # U or UNICODE <=> (?u)         Make \w, \W, \b, and \B dependent on the Unicode character properties database.
    # X or VERBOSE <=> (?x)         Ignores whitespace outside character sets
    
    #This method is the default action for all pattern in lowest priviledge
    def command_999_default(self, user, message, args):
        """.*?(?s)(?m)"""
        self.replyMessage(user, message)

    ########################################################################################################################
    #These following methods can be only used after bot has been successfully started

    #show : xa,away---away   dnd---busy   available--online
    def setState(self, show, status_text):
        if show:
            show = show.lower()
        if show == "online" or show == "on" or show == "available":
            show = "available"
        elif show == "busy" or show == "dnd":
            show = "dnd"
        elif show == "away" or show == "idle" or show == "off" or show == "out" or show == "xa":
            show = "xa"
        else:
            show = "available"
        
        self.show = show

        if status_text:
            self.status = status_text
        
        if self.conn:
            pres=xmpp.Presence(priority=5, show=self.show, status=self.status)
            self.conn.send(pres)

    def getState(self):
        return self.show, self.status

    def replyMessage(self, user, message):
        self.conn.send(xmpp.Message(user, message))

    def getRoster(self):
        return self.conn.getRoster()

    def getResources(self, jid):
        roster = self.getRoster()
        if roster:
            return roster.getResources(jid)

    def getShow(self, jid):
        roster = self.getRoster()
        if roster:
            return roster.getShow(jid)

    def getStatus(self, jid):
        roster = self.getRoster()
        if roster:
            return roster.getStatus(jid)

    def authorize(self, jid):
        """ Authorise JID 'jid'. Works only if these JID requested auth previously. """
        self.getRoster().Authorize(jid)
  
    def system_status(self, jid):
        from datetime import timedelta
        import socket
        import urllib2

        # System temperature
        with open("/sys/class/thermal/thermal_zone0/temp") as Te:
            Te = float(Te.read()[:-1])/1000.0
            temp_string = str("Temperature: %.1f C" %(Te))
        
        # Uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = str(timedelta(seconds = uptime_seconds))
            uptime_string = str("Uptime: %s "%(uptime_string.split('.')[0]))
        
        with open('/proc/meminfo', 'r') as f:
            fr = f.readlines()
            MemTotal  = float(fr[0].split(':')[-1].split('kB')[0].replace(' ',''))
            MemFree   = float(fr[1].split(':')[-1].split('kB')[0].replace(' ',''))
            MemBuffer = float(fr[2].split(':')[-1].split('kB')[0].replace(' ',''))
            MemCached = float(fr[3].split(':')[-1].split('kB')[0].replace(' ',''))

            MemUsed = MemTotal-MemFree-MemBuffer-MemCached
            mem_string = str("Used memory: %d/%d mb" %(0.001*MemUsed,0.001*MemTotal))

        private_ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close())\
            for s in [socket.socket(socket.AF_INET,socket.SOCK_DGRAM)]][0][1]
        
        public_ip  = urllib2.urlopen('http://ip.42.pl/raw').read()

        publicip_string = str("Public IP: %s" %public_ip)
        privateip_string = str("Private IP: %s" %private_ip)

        Summary = '\n'.join([\
            "System Status: ",\
            temp_string,\
            uptime_string,\
            mem_string,\
            privateip_string,\
            publicip_string])

        return(Summary)
        

    def send_file(self, jid, filepath):
        ibb = xmpp.filetransfer.IBB()
        ibb.PlugIn(self.conn)
        f = open(filepath)
        
        print('Sending file...') 
        print('To: '+jid.getStripped())
        print('From: '+jid.getNode())
        print('File: '+filepath)

        ibb.OpenStream(jid.getNode(), jid.getStripped()+'/resource', f)
  
    def send_file_byemail(self, jid, filepath, account):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText        

        msg = MIMEMultipart('alternative')
        s = smtplib.SMTP('smtp.gmail.com', 587)
        
        s.ehlo()
        s.starttls()
        s.ehlo()
        
        s.login(account['username'], account['password'])
        msg['Subject'] = 'Here you have the image'
        msg['From'] = account['username']
        body = 'Please, see in the attatchments the image'
        content = MIMEText(body, 'plain')
        msg.attach(content)

        f = file(filepath)
        attachment = MIMEText(f.read())
        attachment.add_header(\
            'Content-Disposition',\
            'attachment',\
            filename=filepath.split('/')[-1])
        
        msg.attach(attachment)
        
        s.sendmail(account['username'],account['admin'],msg.as_string())


    ########################################################################################################################
    def initCommands(self):
        if self.commands:
            self.commands.clear()
        else:
            self.commands = list()
        for (name, value) in inspect.getmembers(self):
            if inspect.ismethod(value) and name.startswith(self.command_prefix):
                self.commands.append((value.__doc__, value))
        #print self.commands

    def controller(self, conn, message):
        text = message.getBody()
        user = message.getFrom()
        if text:
            text = text.encode('utf-8', 'ignore')
            if not self.commands:
                self.initCommands()
            for (pattern, bounded_method) in self.commands:
		print "Testing [%s] against regex [%s]\n" % (text, pattern)
                match_obj = re.match(pattern, text)
                if(match_obj):
                    try:
                        return_value = bounded_method(user, text, match_obj.groups())
                        if return_value == self.GO_TO_NEXT_COMMAND:
                            pass
                        else:
                            break
                    except:
                        print_info(sys.exc_info())
                        self.replyMessage(user, traceback.format_exc())

    def presenceHandler(self, conn, presence):
        #print presence
        #print_info(presence)
        if presence:
            print "-"*100
            print presence.getFrom(), ",", presence.getFrom().getResource(), ",", presence.getType(), ",", presence.getStatus(), ",", presence.getShow()
            print "~"*100
            if presence.getType()=='subscribe':
                jid = presence.getFrom().getStripped()
                self.authorize(jid)

    def StepOn(self):
        try:
            self.conn.Process(1)
        except KeyboardInterrupt: 
            return 0
        return 1

    def GoOn(self):
        while self.StepOn(): pass

    ########################################################################################################################
    # "debug" parameter specifies the debug IDs that will go into debug output.
    # You can either specifiy an "include" or "exclude" list. The latter is done via adding "always" pseudo-ID to the list.
    # Full list: ['nodebuilder', 'dispatcher', 'gen_auth', 'SASL_auth', 'bind', 'socket', 'CONNECTproxy', 'TLS', 'roster', 'browser', 'ibb'].
    def __init__(self, server_host="talk.google.com", server_port=5222, debug=[]):
        self.debug = debug
        self.server_host = server_host
        self.server_port = server_port

    def start(self, gmail_account, password):
        jid=xmpp.JID(gmail_account)
        user, server, password = jid.getNode(), jid.getDomain(), password
        
        self.conn=xmpp.Client(server, debug=self.debug)
        #talk.google.com
        conres=self.conn.connect( server=(self.server_host, self.server_port) )
        if not conres:
            print "Unable to connect to server %s!"%server
            sys.exit(1)
        if conres<>'tls':
            print "Warning: unable to estabilish secure connection - TLS failed!"
        
        authres=self.conn.auth(user, password)
        if not authres:
            print "Unable to authorize on %s - Plsese check your name/password."%server
            sys.exit(1)
        if authres<>"sasl":
            print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server
        
        self.conn.RegisterHandler("message", self.controller)
        self.conn.RegisterHandler('presence',self.presenceHandler)
        
        self.conn.sendInitPresence()
        
        self.setState(self.show, self.status)
        
        print "Bot started."
        self.GoOn()

    ########################################################################################################################


############################################################################################################################
if __name__ == "__main__":
    bot = GtalkRobot()
    bot.setState('available', "PyGtalkRobot")
    bot.start("username@gmail.com", "password")
