#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------
# Copyright (c) 2010-2017 Denis Machard
# This file is part of the extensive testing project
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA
# -------------------------------------------------------------------

import base64
import zlib
try:
    # python 2.4 support
    import simplejson as json
except ImportError:
    import json

import AgentServerInterface as ASI
import EventServerInterface as ESI
import Context
import Common

from Libs import Settings, Logger

import ConfigParser
import os
import signal
import shlex
import subprocess
import sys
import time
import shutil
import tarfile


class AgentsManager(Logger.ClassLogger):    
    def __init__(self):
        """
        Construct Probes Manager
        """
        self.pkgsAgentsPath = "%s/%s/%s/linux2/" % ( Settings.getDirExec(),   Settings.get( 'Paths', 'packages' ), 
                                        Settings.get( 'Paths', 'agents' ) )

        self.configsFile = None
        self.__pids__ = {}

    def encodeData(self, data):
        """
        Encode data
        """
        ret = ''
        try:
            tasks_json = json.dumps(data)
        except Exception as e:
            self.error( "Unable to encode in json: %s" % str(e) )
        else:
            try: 
                tasks_zipped = zlib.compress(tasks_json)
            except Exception as e:
                self.error( "Unable to compress: %s" % str(e) )
            else:
                try: 
                    ret = base64.b64encode(tasks_zipped)
                except Exception as  e:
                    self.error( "Unable to encode in base 64: %s" % str(e) )
        return ret

    def getStats(self, b64=False):
        """
        Constructs some statistics on agents
            - Licence definition

        @return: agents statistics
        @rtype: dict
        """
        ret= {}
        try:
            ret['max-reg'] = Context.instance().getLicence()[ 'agents' ] [ 'instance' ]
            ret['max-def'] = Context.instance().getLicence()[ 'agents' ] [ 'default' ]
        except Exception as e:
            self.error( "unable to get agents stats: %s" % e )
        else:
            if b64:
                ret = self.encodeData(data=ret)
        return ret

    def getDefaultAgents(self, b64=False):
        """
        Read default agents to start on boot

        @return: agents to start on boot
        @rtype: list
        """
        agents = []
        if not os.path.isfile( "%s/agents.ini" % Settings.getDirExec() ):
            self.error( 'config file (agents.ini) is missing' )
        else:
            self.configsFile = ConfigParser.ConfigParser()
            self.configsFile.read( "%s/agents.ini" % Settings.getDirExec() )
            for p in self.configsFile.sections():
                tpl = {'name': p }
                for optKey,optValue in self.configsFile.items(p):
                    tpl[optKey] = optValue
                # {'enable': '1', 'type': 'textual', 'name': 'textual01', 'description': 'default probe'},
                agents.append( tpl )  
        if b64:
            agents = self.encodeData(data=agents)
        return agents

    def addDefaultAgent(self, aName, aType, aDescr):
        """
        Add default agent

        @type  aName:
        @param aName:

        @type  aType:
        @param aType:

        @type  aDescr:
        @param aDescr:

        @return:
        @rtype: boolean
        """
        ret = Context.CODE_ERROR
        try:
            if self.configsFile is not None:
                # check licence
                if len(self.configsFile.sections()) >=  Context.instance().getLicence()[ 'agents' ] [ 'default' ]:
                    ret = Context.CODE_FORBIDDEN
                else:
                    # add the section in the config file object
                    self.configsFile.add_section(aName)
                    self.configsFile.set( aName, 'enable', 1)
                    self.configsFile.set( aName, 'type', aType)
                    self.configsFile.set( aName, 'description', aDescr)
                    
                    # write date the file 
                    f = open(  "%s/agents.ini" % Settings.getDirExec() , 'w')
                    self.configsFile.write(f)
                    f.close()

                    # notify all admin and tester
                    notif = ( 'agents-default', ( 'add', self.getDefaultAgents() ) )
                    ESI.instance().notifyByUserTypes(body = notif, admin=True, leader=False, tester=True, developer=False)
                    
                    # return OK
                    ret = Context.CODE_OK
        except ConfigParser.DuplicateSectionError:
            self.error( "agent already exist %s" % str(aName) ) 
            ret = Context.CODE_ALLREADY_EXISTS
        except Exception as e:
            self.error( "unable to add default agent: %s" % str(e) )
            ret = Context.CODE_FAILED
        return ret
    
    def delDefaultAgent(self, aName):
        """
        Delete default agent

        @type  aName:
        @param aName:

        @return:
        @rtype: boolean
        """
        ret = Context.CODE_ERROR
        try:
            if self.configsFile is not None:
                # remove the section in the config file object
                self.configsFile.remove_section(aName)

                # write date the file 
                f = open(  "%s/agents.ini" % Settings.getDirExec() , 'w')
                self.configsFile.write(f)
                f.close()

                # notify all admin and tester
                notif = ( 'agents-default', ( 'del', self.getDefaultAgents() ) )
                ESI.instance().notifyByUserTypes(body = notif, admin=True, leader=False, tester=True, developer=False)

                runningAgent = ASI.instance().getAgent(aname=aName)
                if runningAgent is not None:
                    runningAgent['auto-startup'] = False
                notif2 = ( 'agents', ( 'del', ASI.instance().getAgents() ) )
                ESI.instance().notifyByUserTypes(body = notif2, admin=True, leader=False, tester=True, developer=False)


                # return OK
                ret = Context.CODE_OK
        except ConfigParser.NoSectionError:
            self.error( "agent not found: %s" % str(aName) )    
            ret = Context.CODE_NOT_FOUND
        except Exception as e:
            self.error( "unable to delete default agent: %s" % str(e) )
            ret = Context.CODE_FAILED
        return ret

    def getRunning (self, b64=False):
        """
        Returns all registered agent

        @return: all registered agent
        @rtype: list
        """
        self.trace("get running agents" )
        ret = ASI.instance().getAgents()
        if b64:
            ret = self.encodeData(data=ret)
        return ret

    def getInstalled (self, b64=False):
        """
        Returns all registered agents

        @return: all registered agents
        @rtype: list
        """
        self.trace("get agents installed" )
        pluginsInstalled = []
        if os.path.exists( '%s/%s/Embedded/' % ( Settings.getDirExec(), Settings.get( 'Paths', 'tools' )) ):
            files = os.listdir( '%s/%s/Embedded/' % ( Settings.getDirExec(), Settings.get( 'Paths', 'tools' )) )
            for f in files:
                if f.endswith('Agent.py'):
                    a = {}
                    # open plugin to get agent type and description
                    fp = open( '%s/%s/Embedded/%s' % (Settings.getDirExec(), Settings.get( 'Paths', 'tools' ), f) , 'r')
                    data = fp.read()
                    fp.close()
                    #
                    agentType = data.split('__TYPE__="""')
                    if len(agentType) == 2:
                        agentType = agentType[1].split('"""', 1)[0]
                        a['type'] = agentType
                    agentDescr = data.split('__DESCRIPTION__="""')
                    if len(agentDescr) == 2:
                        agentDescr = agentDescr[1].split('"""', 1)[0]
                        a['description'] = agentDescr
                    if  len(a) > 0:
                        pluginsInstalled.append( a )
        if b64:
            pluginsInstalled = self.encodeData(data=pluginsInstalled)
        return pluginsInstalled

    def disconnectAgent(self, name):
        """
        Disconnect agent
        """
        self.info( "Disconnect agent Name=%s" % name )
        if not name in ASI.instance().agentsRegistered:
            self.trace( "disconnect agent, agent %s not found" % name )
            return Context.CODE_NOT_FOUND
        else:
            agentProfile =  ASI.instance().agentsRegistered[name]
            ASI.instance().stopClient(client=agentProfile['address'] )
        return Context.CODE_OK

    def stopAgent(self, aname):
        """
        Stop the agent gived in argument

        @type  aname:
        @param aname:

        @return: 
        @rtype: 
        """
        self.trace( "stop agent %s" % aname )
        ret = False
        try:
            client = ASI.instance().getAgent( aname=aname )
            if client is None:
                self.trace( "agent %s not found" % aname )
                ret = False
            else:
                self.trace( "agent %s found" % aname )
                # Stop remote agents or manual: start a agent manually is equal to a remote agent
                if not client['auto-startup']:
                    ASI.instance().stopClient( client = client['address'] )
                else:
                    # Stop local agent
                    if aname in self.__pids__:
                        try:
                            p = self.__pids__[aname]
                            p_id = p.pid
                            os.kill(p_id, signal.SIGKILL)
                            p.wait()
                            self.__pids__.pop(aname)
                        except Exception as e:
                            self.error( "Unable to kill %d: %s" % (p_id, str(e)) )
                    else:
                        self.error( "agent not found on pids: %s" % aname )
                ret = True
        except Exception as e:
            self.error( "unable to stop agent: %s" % e )
        return ret

    def startAgent(self, atype, aname, adescr, adefault=False):
        """
        Start the agent passed as argument

        @type  atype:
        @param atype:

        @type  aname:
        @param aname:

        @type  adescr:
        @param adescr:

        @type  adefault:
        @param adefault:

        @return: 
        @rtype: 
        """
        ret = -1
        try:
            self.trace( "start agent %s of type %s" % (aname,atype) )
            controllerIp = Settings.get( 'Bind', 'ip-asi' )
            controllerPort = Settings.get( 'Bind', 'port-asi' )
            sslSupport = False
            if int(Settings.get( 'Agent_Channel', 'channel-ssl' )): sslSupport = True
            __cmd_str__ = "%s/%s/toolagent '%s' '%s' '%s' '%s' '%s' '%s' %s" % ( 
                                                                Settings.getDirExec(), Settings.get( 'Paths', 'tools' ),
                                                                controllerIp,
                                                                controllerPort,
                                                                sslSupport,
                                                                atype, 
                                                                aname,
                                                                adescr,
                                                                adefault
                                                            ) 
            self.trace( "call %s" % __cmd_str__ )
            __cmd_args__ = shlex.split( __cmd_str__ )   
            p = subprocess.Popen(__cmd_args__, stdin=sys.stdout, stdout=sys.stdout, stderr=sys.stdout ) 
            time.sleep(1) # not clean at all....
            ret = p.poll()
            if ret is None:
                self.__pids__[aname] = p
            self.trace( "start agent, return code %s" % ret ) 
            if ret is None:
                ret = 0
        except Exception as e:
            self.error( "unable to start properly: %s" % e )
        return ret

    def trace(self, txt):
        """
        Trace message
        """
        Logger.ClassLogger.trace(self, txt="ATM - %s" % txt)

###############################
AM = None
def instance ():
    """
    Returns the singleton

    @return: One instance of the class Context
    @rtype: Context
    """
    return AM

def initialize ():
    """
    Instance creation
    """
    global AM
    AM = AgentsManager()

def finalize ():
    """
    Destruction of the singleton
    """
    global AM
    if AM:
        AM = None