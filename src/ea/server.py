#!/usr/bin/python

# -------------------------------------------------------------------
# Copyright (c) 2010-2021 Denis Machard
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -------------------------------------------------------------------

"""
Provide cli usage of the server
"""

from optparse import OptionParser
import sys
import platform

from ea.serverengine import AutomationServer as Core
from ea.servercontrols import CliFunctions as Cli

# checking python version before to start the server
if sys.version_info[0] == 2:
    if sys.version_info[1] <= 6:
        print("Python %s not supported" % platform.python_version())
        sys.exit(2)
elif sys.version_info[0] == 3:
    if sys.version_info[1] < 5:
        print("Python %s not supported" % platform.python_version())
        sys.exit(2)
else:
    print("Python %s not supported" % platform.python_version())
    sys.exit(2)

# prepare the command line with all options
parser = OptionParser()

parser.add_option('--start', dest='start', default=False,
                  action='store_true',
                  help="Start the server.")
if platform.system() == "Linux":
    parser.add_option('--stop', dest='stop', default=False,
                      action='store_true',
                      help="Stop the server.")
    parser.add_option('--status', dest='status', default=False,
                      action='store_true',
                      help='Show the current status of the server.')
    parser.add_option('--reload', dest='reload', default=False,
                      action='store_true',
                      help='Reload the configuration of the server.')
parser.add_option('--version', dest='version', default=False,
                  action='store_true',
                  help='Show the version.')
parser.add_option('--generate-api-key', dest='apikey', default=False,
                  action='store_true',
                  help='Generate key for rest api (argument: <username>)')
parser.add_option('--show-api-secret', dest='apisecret', default=False,
                  action='store_true',
                  help='Get api secret for user <username>')
parser.add_option('--decode-trx', dest='decodetrx', default=False,
                  action='store_true',
                  help='Decode trx file (argument: <file>)')
parser.add_option('--install-adapter', dest='install_adapter', default=False,
                  action='store_true',
                  help='Install sut adapter (argument: <plugin name>)')
parser.add_option('--convert-to-yaml', dest='convert2yaml', default=False,
                  action='store_true',
                  help='Convert XML files to YAML')
parser.add_option('--show-data-path', dest='datastorage', default=False,
                  action='store_true',
                  help='Show the path of the datastorage')
parser.add_option('--generate-token', dest='generate_token', default=False,
                  action='store_true',
                  help='Generate token for remote agent <name>')
parser.add_option('--delete-token', dest='delete_token', default=False,
                  action='store_true',
                  help='Delete token by <name>')
parser.add_option('--list-tokens', dest='list_tokens', default=False,
                  action='store_true',
                  help='List all tokens')
(options, args) = parser.parse_args()


def cli():
    """
    Function to control the server according to the argument
    provided
    """
    Core.initialize()

    if platform.system() == "Linux":

        if options.stop is True:
            Core.stop()
            sys.exit(0)

        if options.status is True:
            Core.status()
            sys.exit(0)

        if options.reload is True:
            Cli.instance().reload()
            sys.exit(0)

    if options.start is True:
        Core.start()
        sys.exit(0)

    if options.version is True:
        Cli.instance().version()
        sys.exit(0)

    if options.apikey is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().generateKey(username=args[0])
        sys.exit(0)

    if options.apisecret is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().getSecret(username=args[0])
        sys.exit(0)
        
    if options.decodetrx is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().decodeTrx(filename=args[0])
        sys.exit(0)

    if options.install_adapter is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().installAdapter(name=args[0])
        sys.exit(0)
        
    if options.convert2yaml is True:
        Cli.instance().convert2yaml()
        sys.exit(0)
        
    if options.datastorage is True:
        Cli.instance().show_data_storage()
        sys.exit(0)
        
    if options.generate_token is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().generate_token(token_name=args[0])
        sys.exit(0)

    if options.delete_token is True:
        if not args:
            parser.print_help()
            sys.exit(2)
        Cli.instance().delete_token(token_name=args[0])
        sys.exit(0)
        
    if options.list_tokens is True:
        Cli.instance().list_tokens()
        sys.exit(0)
        
    parser.print_help()
    sys.exit(2)
