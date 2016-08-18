from twisted.application import internet, service
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from random import randint

class Bet(object):

    def __init__(self):
        self.quantity = 0
        self.digit = 0

class Player(object):

    #STATES:
    #0 - Not ID Associated
    #1 - Not Yet Played
    #2 - Playing
    #3 - Played

    def __init__(self):
        self.id = 0
        self.state = 0
        self.called = False
        self.bet = None
        self.earnings = 0.0
        self.protocol = None

class GameState(object):

    #STATES:
    #0 - Not Started
    #1 - Playing

    def __init__(self):
        self.players = []
        self.acceptedPlayerIDs = []
        self.playerList = []
        self.currentBet = []
        self.currentPlayerID = 0
        self.round = 1
        #host is given ability to start game
        self.host = None
        self.state = 0

    def updateAcceptedPlayers(self, newID):
        for player in self.players:
            idString = str(newID)
            player.protocol.transport.write("1::", len(idString), "::", idString)

    def updatePlayer(self, player):
        self.players.append(player)
        if len(self.players.count) == 1:
            self.host = player

    def beginGame():
        print "Begin Game"
        randint(0, len(self.acceptedPlayerIDs))
