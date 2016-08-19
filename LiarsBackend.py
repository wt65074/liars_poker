from twisted.application import internet, service
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from random import randint
import sys

class MultiEcho(Protocol):

    def __init__(self, factory, player):
        log.msg("New Protocol")
        self.factory = factory
        self.player = player
        self.inputBuffer = ""

    #filters out late connections and updates players on who is part of the game
    def connectionMade(self):
        self.transport.write("Connected")

        if self.factory.gameState.state != 0:
            self.transport.loseConnection()
            return

        #right away we need to let them know who else has been invited to the game and who has accepted but after they id

    def handleData(self, dataType, data):

        #TYPES
        #0 - players
        #1 - id
        #2 - host instruction
        #3 - move

        #if the player is not the current player and the game has started return
        #the players have no data if it is not their turn except their identification
        if self.factory.gameState.currentPlayer != self.player and self.factory.gameState.state != 0:
            return

        #game not started, only host can send message
        #once a player connects, they can do nothing else until the game starts
        if self.factory.gameState.state == 0 and self.factory.gameState.host != self.player:
            return

        #if the player has not identified themselves return
        #every player must first identify themselves, except the host
        if self.player.id == 0 and (dataType != 1 or dataType != 0):
            return

        #Invited players list
        if dataType == 0:

            #Data should come in id+username|id+username
            for string in data.split("|"):
                self.factory.gameState.playerList += string

        #identification type
        elif dataType == 1:
            if not data.isdigit():
                return
            identification = int(data)
            self.player.id = identification
            #inform all players that there has been a new identificatioin
            self.factory.gameState.updateAcceptedPlayers(identification)

        #host type
        #the only host date ever sent is a begin game call
        elif dataType == 2:

            self.factory.gameState.beginGame()

        #game play type
        elif dataType == 3:
            print "Data Type 2"
            #game play syntax
            #BET+Number+Digit
            #CALL

            if data == "CALL":
                #let everyone know call
                self.factory.gameState.sendCall()
            else:
                betData = data.split("+")
                number = betData[0]
                digit = betData[1]

                #let everyone know that there was a bet
                self.factory.gameState.sendBet(Bet(number, digit))
                self.factory.gameState.bettingPlayer = self.player

        else:
            print "Unknown Data Type"



        print dataType, dataLength, data

    def parse_data(self, data):

        self.inputBuffer += data

        if '::' not in self.inputBuffer:
            return

        continueLoop = True

        while continueLoop == True:

            print "Loop"
            print self.inputBuffer

            continueLoop = False

            toDelete = 0

            #do not have enough data to parse
            #return and wait till more data is sent
            if len(self.inputBuffer.split("::")) < 3:
                print "Not enough data dividers"
                return
            if len(self.inputBuffer.split("::")) >= 5:
                #greate than 5 because they will run together
                continueLoop = True

            splitString = self.inputBuffer.split("::")

            toDelete += 4

            if not splitString[0].isdigit():
                #impliment better error handling
                print "0 is not digit"
                return

            if not splitString[0].isdigit():
                #implemet better error handling
                print "1 is not digit"
                return

            print "Stuff is digi"

            toDelete += len(splitString[0])
            toDelete += len(splitString[1])

            dataType = int(splitString[0])
            dataLength = int(splitString[1])
            #get the correct number of data from data, if it isnt enough it will return the length of the string
            parsedData = splitString[2][0:dataLength]

            if len(parsedData) < dataLength:
                #not enough data in buffer
                #return and wait till more data is sent
                print len(parsedData)
                return

            toDelete += len(parsedData)
            print(toDelete)
            self.inputBuffer = self.inputBuffer[toDelete:len(self.inputBuffer)]
            self.handleData(dataType, parsedData)

    def dataReceived(self, data):

        #data format
        #data type::data length::content
        print "Data Recieved", data
        self.parse_data(data)

    def connectionLost(self, reason):
        #remove player from game
        #need to update player list here
        print "Drop Connection"
        if self.player in self.factory.gameState.players:
            self.factory.gameState.players.remove(self)

class MultiEchoFactory(Factory):

    def __init__(self, gameState):
        self.echoers = []
        self.gameState = gameState
        #log.startLogging(sys.stdout)

    def buildProtocol(self, addr):
        print "Build Protocol"
        #players arent entered into the game state until they identify
        newPlayer = Player()
        toReturn = MultiEcho(self, newPlayer)
        newPlayer.Protocol = toReturn
        return toReturn

class Bet(object):

    def __init__(self, _quantity, _digit):
        self.quantity = _quantity
        self.digit = _digit

    def string():
        return str(self.quantity) + "+" + str(self.digit)

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

        #stores player objects that have been id'd
        self.players = []
        #stores ids of players that have accepted
        self.acceptedPlayerIDs = []
        #stores ids and names of players that were invited
        self.playerList = []

        self.currentBet = None
        self.playersSerials = {}
        self.bettingPlayer = None
        self.currentPlayer = None
        self.round = 1
        #host is given ability to start game
        self.host = None
        self.state = 0

    def sendBet(self, bet):
        self.currentBet = bet
        betString = bet.string()
        for player in self.players:
            player.protocol.transport.write("4::", str(len(betString)), "::", betString)
        self.incrementTurn()

    def sendCall(self):
        for player in self.players:
            player.protocol.transport.write("5::4::CALL")
        self.incrementTurn()

    def updateAcceptedPlayers(self, newID):
        for player in self.players:
            idString = str(newID)
            player.protocol.transport.write("1::", len(idString), "::", idString)

    def updatePlayer(self, player):
        self.players.append(player)
        if len(self.players.count) == 1:
            self.host = player

        if self.player != self.gameState.host:
            #start by writing all the invited names and ids
            playerString = "|".join(self.gameState.playerList)
            player.protocol.transport.write("0::", len(playerString), "::", playerString)
            #then send all the accepted ids to be cross referened
            acceptedString = "|".join(self.gameState.acceptedPlayerIDs)
            player.protocol.transport.write("1::", len(acceptedString), "::", acceptedString)

    def sendNewDollars(self):
        self.playersSerials = {}
        for player in self.players:
            newDollar = self.generateDollar
            self.playersSerials[str(player.id)] = newDollar

        playerSerialsString = '|'.join(['%s+%s' % (key, value) for (key, value) in stringOfIDs.items()])
        for player in self.players:
            player.protocol.transport.write("6::", len(playerSerialsString), "::", playerSerialsString)

    def getRoundResult(self):

        self.round = self.round + 1
        self.bettingPlayer = None
        self.currentBet = None

        # ALL THAT needs to happen here is changing the api values

        #occurances = 0
        #digit = str(self.currentBet.digit)

        #for playerID, dollar in playersSerials.iteritems():
            #dollarString = str(dollar)
            #occurances += dollarString.count(digit)

        #if occurances >= self.currentBet.number:
            #the better wins
            #for player in self.players:
                #if player == bettingPlayer:
                    #player.protocol.transport.write("7::3::WIN")



    def incrementTurn():

        if self.players.index(self.currentPlayer) == len(self.players) - 1:
            self.players.currentPlayer = self.players[0]
        else:
            self.players.currentPlayer = self.players[self.players.index(self.currentPlayer) + 1]

        if self.bettingPlayer == self.currentPlayer:
            #the round has been played through and we can evaluate the result
            self.getRoundResult()

    def generateDollar():
        return randint(0, 10000000)

    def beginGame():

        print "Begin Game"

        orderedArray = []
        tempIDs = self.acceptedPlayerIDs

        #loop until the entire array is filled
        while len(orderedArray) != len(self.acceptedPlayerIDs):
            #generate a random in from the remaining indexes
            index = randint(0, len(tempIDs))
            orderedArray.append(tempIDs[index])
            del tempIDs[index]

        tempPlayers = []

        #get the array of players ordered
        for identifier in orderedArray:
            for player in self.players:
                if player.identifier == identifier:
                    tempPlayers.append(player)

        self.players = tempPlayers
        self.currentPlayer = self.players[0]

        #need to return the ordered ids
        stringOfIDs = "|".join(self.orderedArray)
        for player in self.players:
            newDollar = self.generateDollar
            self.playersSerials[str(player.id)] = newDollar
            player.protocol.transport.write("3::", len(stringOfIDs), "::", stringOfIDs)

        playerSerialsString = '|'.join(['%s+%s' % (key, value) for (key, value) in stringOfIDs.items()])
        for player in self.players:
            player.protocol.transport.write("6::", len(playerSerialsString), "::", playerSerialsString)
