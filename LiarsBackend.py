from twisted.application import internet, service
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.python import log
from random import randint
import json
import sys

def generateDataString(dataType, data):

    #get the number of digits and the zeros to append to dataType to make it 4 digits
    zeros = "0" * (4 - len(str(dataType)))

    #create a string from the zeros and the dataType
    dataTypeString = zeros + str(dataType)

    #create the content string
    contentString = dataTypeString + data

    #get the length of the content
    contentLength = len(contentString)

    #get a string of zeros to make a 4 digit number
    zeros = "0" * (4 - len(str(contentLength)))

    #create the string from zeros and content length
    lengthString = zeros + str(contentLength)

    print lengthString + contentString

    return lengthString + contentString

class MultiEcho(Protocol):
    def __init__(self, factory, player):
        print("New Protocol")
        self.factory = factory
        self.player = player
        self.inputBuffer = ""
    def connectionMade(self):
        print("New connection")
        if self.factory.gameState.state != 0:

            # We drop any connections made after the game is started
            # We hold off on sending the rest of the player list until the id is confirmed as part of the game

            self.transport.loseConnection()
            return
    def handleData(self, dataType, data):

        #TYPES
        #1 - players
        #2 - id
        #3 - host instruction
        #4 - move
        print "ID" + str(self.player.id) + "Handle Data " + str(dataType) + " " + data
        # If the player is not the current player and the game has started return
        # The players have no data if it is not their turn except their identification
        if self.factory.gameState.currentPlayer != self.player and self.factory.gameState.state != 0:
            print "not current"
            return

        # Game not started, only host can send message
        # Once a player connects, they can do nothing else until the game starts

        # If the player has not identified themselves return
        # Every player must first identify themselves, except the host
        if self.player.id == 0 and (dataType != 2 and dataType != 1):
            print "worng"
            return

        # INVITED PLAYER LIST ------------------
        # Player identification list is recieved in the form id+name+pushtoken|id+name+pushtoken
        if dataType == 1:

            print "Player ID List recieved"

            tokens = []

            #id+name+pushtoken|id+name+pushtoken
            for string in data.split("|"):
                # Save entire identification string
                self.factory.gameState.playerList.append(string)



                # Forward the deviceTokens so the json can be dumped
                #tokens += string.split("+")[2]
            print "New Player List" + str(self.factory.gameState.playerList)
            # Save deviceTokens as json and execute push notifiations
            #self.factory.gameState.dumpPlayerDeviceTokens(tokens)

        # PLAYER IDENTIFICATION -------------------
        # Player identification is sent in
        # We can now send the list of the rest of the players in the game to the player
        elif dataType == 2:
            #if not data.isdigit():
                #return
            identification = int(data)
            print "New ID" + str(identification)
            self.player.id = identification
            self.transport.write(generateDataString(7, "ID"))

            for _player in self.factory.gameState.players:
                self.transport.write(generateDataString(1, str(_player.id)))

            # Inform all players that there has been a new identificatioin by sending a new id
            # Add this players id to the array of accepted players
            self.factory.gameState.updatePlayer(self.player)

        # BEGIN GAME -----------------------
        elif dataType == 3:

            self.factory.gameState.beginGame()

        # GAME PLAY TYPE (CALL OR BET) ---------------
        elif dataType == 4:
            print "Data Type 2"
            #game play syntax
            #BET - Number+Digit
            #CALL

            if data == "CALL":
                #let everyone know call
                self.factory.gameState.sendCall(self.player)
            else:

                betData = data.split("+")
                number = betData[0]
                digit = betData[1]

                if not number.isdigit():
                    print "Number is not digit"
                    return
                if not digit.isdigit():
                    print "Digit is not digit"
                    return

                #let everyone know that there was a bet
                self.factory.gameState.bettingPlayer = self.player
                self.factory.gameState.sendBet(Bet(number, digit), self.player)

        else:
            print "Unknown Data Type"



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

            if not splitString[1].isdigit():
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
        print "New Factory"
        self.echoers = []
        self.gameState = gameState
        #log.startLogging(sys.stdout)

    def buildProtocol(self, addr):
        print "Build Protocol"
        #players arent entered into the game state until they identify
        toReturn = MultiEcho(self, Player())
        toReturn.player.protocol = toReturn
        return toReturn

class Bet(object):

    def __init__(self, _quantity, _digit):
        self.quantity = _quantity
        self.digit = _digit

    def string(self):
        return str(self.quantity) + "+" + str(self.digit)

class Player(object):

    #STATES:
    #0 - Not ID Associated
    #1 - Not Yet Played
    #2 - Playing
    #3 - Played

    def __init__(self):

        #identification information
        self.id = 0
        self.name = ""
        self.pushToken = ""


        self.state = 0
        self.called = False
        self.bet = None
        self.earnings = 0.0
        self.protocol = None

class GameState(object):

    #STATES:
    #0 - Not Started
    #1 - Playing
    def __init__(self, _port):

        # Stores player objects that have been id'd and thus accepted
        self.players = []

        # Stores id+name+pushtoken|id+name+pushtoken for each user
        self.playerList = []

        self.currentBet = None
        # Stores id:serialnumber(int)
        self.playersSerials = {}
        self.bettingPlayer = None
        self.currentPlayer = None
        self.round = 1
        #host is given ability to start game
        self.host = None
        self.state = 0
        self.port = _port

    # Make sure submitted ids were invited to the game
    def verifyID(self, idToVerify):
        idVerified = False
        for string in playerList:
            existingID = string.split("+")[0]
            if existingID.isdigit():
                if int(existingID) == idToVerify:
                    idVerified = True

        return idVerified

    def updatePlayer(self, player):

        print "New iD to send " + str(player.id)
        for _player in self.players:
            print "Player recieving ID " + str(_player.id)
            _player.protocol.transport.write(generateDataString(1, str(player.id)))
        # add player to players

        self.players.append(player)

        # if the player is the first player in the party make it the host
        if len(self.players) == 1:
            self.host = player
            return

        # write a list of all the player strings to the new player
        playerString = "|".join(self.playerList)
        player.protocol.transport.write(generateDataString(0, playerString))

        #then send all the accepted ids to be cross referened

    def sendBet(self, bet, betPlayer):
        self.currentBet = bet
        betString = bet.string()
        for player in self.players:
            if player != betPlayer:
                player.protocol.transport.write(generateDataString(4, betString))
        self.incrementTurn()

    def sendCall(self, callPlayer):
        for player in self.players:
            if player != callPlayer:
                player.protocol.transport.write(generateDataString(5, "CALL"))

        self.incrementTurn()

    def sendNewDollars(self):
        self.playersSerials = {}
        for player in self.players:
            newDollar = self.generateDollar()
            self.playersSerials[str(player.id)] = newDollar
        # SEND SERIAL NUMBERS TO players
        arrayOfStrings = []
        for (key, value) in self.playersSerials.iteritems():
            string = '%s+%s' % (key, str(value))
            arrayOfStrings.append(string)
        playerSerialsString = '|'.join(arrayOfStrings)
        for player in self.players:
            player.protocol.transport.write(generateDataString(6, playerSerialsString))

    def getRoundResult(self):

        self.round = self.round + 1
        self.bettingPlayer = None
        self.currentBet = None

        self.sendNewDollars()

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

    def incrementTurn(self):

        if self.players.index(self.currentPlayer) == len(self.players) - 1:
            self.currentPlayer = self.players[0]
        else:
            self.currentPlayer = self.players[self.players.index(self.currentPlayer) + 1]

        if self.bettingPlayer == self.currentPlayer:
            #the round has been played through and we can evaluate the result
            self.getRoundResult()

    def generateDollar(self):
        tens = 10000000
        dollar = 0
        for i in xrange(8):
            dollar += randint(0, 9) * tens
            tens = tens / 10

        return dollar

    def beginGame(self):

        print "Begin Game"

        orderedArray = []
        tempPlayers = self.players

        # RANDOMIZE ORDER OF GAME

        print "Self Player To Arrange " + str(tempPlayers)

        #loop until the entire array is filled
        while len(tempPlayers) > 0:
            #generate a random int from the remaining indexes
            print "Player Length " + str(len(tempPlayers))
            index = randint(0, len(tempPlayers) - 1)
            #add random player to array
            orderedArray.append(tempPlayers[index])
            del tempPlayers[index]

        self.players = orderedArray

        # get current player
        self.currentPlayer = self.players[0]

        # SEND IDS TO players
        stringOfIDs = ""
        arrayOfIDs = []
        for player in self.players:
            arrayOfIDs.append(str(player.id))
        stringOfIDs = "|".join(arrayOfIDs)

        print "IDs " + stringOfIDs
        for player in self.players:
            newDollar = self.generateDollar()
            self.playersSerials[str(player.id)] = newDollar
            player.protocol.transport.write(generateDataString(3, stringOfIDs))
        print(self.playersSerials)
        # SEND SERIAL NUMBERS TO players
        arrayOfStrings = []
        for (key, value) in self.playersSerials.iteritems():
            string = '%s+%s' % (key, str(value))
            arrayOfStrings.append(string)
            print string
            print arrayOfStrings
        print "STrings" + str(arrayOfStrings)
        playerSerialsString = '|'.join(arrayOfStrings)
        for player in self.players:
            player.protocol.transport.write(generateDataString(6, playerSerialsString))

factory = MultiEchoFactory(GameState(8080))
reactor.listenTCP(8080, factory)
reactor.run()
