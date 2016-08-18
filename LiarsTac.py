from LiarsBackend import *

# configuration parameters
def get_open_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port
port = get_open_port()
iface = 'localhost'
log.msg(port)

# create the listening socket when it is started
gameState = GameState()
factory = MultiEchoFactory(gameState)
tcp_service = internet.TCPServer(port, factory, interface=iface)

application = service.Application("liarspoker")

# this hooks the collection we made to the application
tcp_service.setServiceParent(application)


# at this point, the application is ready to go. when started by
# twistd it will start the child services, thus starting up the
# poetry server

#to run : twistd --python LiarsTac.py
# to kill : kill `cat twistd.pid`
