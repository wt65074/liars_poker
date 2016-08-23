from zope.interface import implements
from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.internet.protocol import ServerFactory, Protocol
from twisted.application import internet, service
from LiarsBackend import *

# Normally we would import these classes from another module.

class Options(usage.Options):

    optParameters = [
        ['port', 'p', None, 'The port number to listen on.'],
        ['storage', 's', None, 'The folder to store player data for push notifications']
    ]

# Now we define our 'service maker', an object which knows
# how to construct our service.

class LiarsServiceMaker(object):

    implements(service.IServiceMaker, IPlugin)

    tapname = "liars"
    description = "A liars service."
    options = Options

    def makeService(self, options):
        gameState = GameState(str(options['storage']), int(options['port']))
        factory = MultiEchoFactory(gameState)
        tcp_service = internet.TCPServer(int(options['port']), factory)

        return tcp_service

# This variable name is irrelevent. What matters is that
# instances of PoetryServiceMaker implement IServiceMaker
# and IPlugin.

service_maker = LiarsServiceMaker()
