from twisted.application import internet, service
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from random import randint
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
import json
import sys
import numpy

def generateDataString(dataType, data):
    # Takes a data type and returns a string in the format:
    # LengthOfData+TypeOfData+Data
    # Where the pluses aren't in the string and the length and type of data is four digits
    # EX: dataType = 1, data = "Example"
    # EX OUTPUT: 00110001Example

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

    print "SENDING STRING: " + lengthString + contentString

    return lengthString + contentString

class MultiEcho(Protocol):

    def __init__(self, factory, player):

        self.factory = factory
        self.player = player
        self.inputBuffer = ""

    def connectionMade(self):
        log.msg("New Connection")
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
        log.msg("ID: " + str(self.player.id) + " Handle Data: Type: " + str(dataType) + "Data: " + data)

        # If the player is not the current player and the game has not started return
        # The players have no data if it is not their turn except their identification
        if self.factory.gameState.currentPlayer != self.player and self.factory.gameState.state != 0:
            print "Player Should Not Be Sending Data"
            print "Reason: Not Their Turn"
            return

        # Game not started, only host can send message
        # Once a player connects, they can do nothing else until the game starts

        # If the player has not identified themselves return
        # Every player must first identify themselves, except the host
        if self.player.id == "" and (dataType != 2 and dataType != 1 and dataType != 0):
            print "Player Should Not Be Sending Data Of This Type"
            print "Reason: Have not send ID"
            return

        # TOKENS TO SEND NOTIFICATION TO ---------
        # Expecting to recived token|token|token
        if dataType == 0:

            tokens = data.split("|")
            self.factory.gameState.sendNotification(tokens)

        # INVITED PLAYER LIST ------------------
        # Player identification list is recieved in the form id+name+username|id+name+username
        if dataType == 1:

            print "Player ID List recieved"

            self.factory.gameState.playerList = data

            log.msg("Player list from host: " + str(self.factory.gameState.playerList))

        # PLAYER IDENTIFICATION -------------------
        # Player identification is sent in
        # We can now send the list of the rest of the players in the game to the player
        elif dataType == 2:
            #if not data.isdigit():
                #return
            identification = str(data)
            log.msg("Player ID'D As: " + str(identification))
            self.player.id = identification

            #notify that the id has been recived
            self.transport.write(generateDataString(7, "ID"))

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

        # Append data to the input buffer
        self.inputBuffer += data

        # Check if we have enough data to split the string
        if '::' not in self.inputBuffer:
            return

        continueLoop = True

        while continueLoop == True:

            continueLoop = False

            toDelete = 0

            if len(self.inputBuffer.split("::")) < 3:
                # We do not have enough data and must wait until more comes in
                print "Not enough data dividers"
                return
            if len(self.inputBuffer.split("::")) >= 5:
                # Set continue look to true because we know we have more than 1 set of data and should continue
                continueLoop = True

            # Split the string
            splitString = self.inputBuffer.split("::")

            # Set the delete to the size
            toDelete += 4

            if not splitString[0].isdigit():
                # The first section of data should be a digit containing the data type
                #impliment better error handling
                return

            if not splitString[1].isdigit():
                # The second section of data should be a digit containing the length of the data
                #implemet better error handling
                return

            # Add the length of the strings to the number of characters we need to delete
            toDelete += len(splitString[0])
            toDelete += len(splitString[1])

            # Set the data type
            dataType = int(splitString[0])
            # Set the data length
            dataLength = int(splitString[1])

            #get the correct number of data from data, if it isnt enough it will return the length of the string
            parsedData = splitString[2][0:dataLength]

            if len(parsedData) < dataLength:
                #not enough data in buffer
                #return and wait till more data is sent
                return

            toDelete += len(parsedData)
            self.inputBuffer = self.inputBuffer[toDelete:len(self.inputBuffer)]
            self.handleData(dataType, parsedData)

    def dataReceived(self, data):

        #data format
        #data type::data length::content
        print "Data Recieved", data
        log.msg("Data Recived", data)
        self.parse_data(data)

    def connectionLost(self, reason):
        #remove player from game
        #need to update player list here
        print "Drop Connection"
        self.factory.gameState.sendLogs()
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
        self.id = ""

        self.state = 0
        self.called = False
        self.bet = None
        self.earnings = 0.0
        self.protocol = None

class GameState(object):

    #STATES:
    #0 - Not Started
    #1 - Playing
    def __init__(self, _storageFolder, _port):

        self.storageFolder = _storageFolder

        # Stores player objects that have been id'd and thus accepted
        self.players = []

        # Stores id+name+pushtoken|id+name+pushtoken
        self.playerList = ""

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


    # Sends an email with the game logs
    def sendLogs(self):

        msg = MIMEMultipart()
        msg['Subject'] = "Game" 
        msg['From'] = "dev.wtobey@gmail.com"
        msg['To'] = "dev.wtobey@gmail.com"

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(self.storageFolder + "/logfile.log", "rb").read())
        Encoders.encode_base64(part)

        part.add_header('Content-Disposition', 'attachment; filename="logfile.log"')

        msg.attach(part)

        try:  
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login("dev.wtobey@gmail.com", "openopenopen")
            server.sendmail("dev.wtobey@gmail.com", "dev.wtobey@gmail.com", msg.as_string())
            server.close()

            print 'Email sent!'
        except:  
            print 'Something went wrong...'


    # Send the players ID to all other players so they know it has joined
    # Send the player all IDs that have been accepted
    def updatePlayer(self, player):

        print "New iD to send " + str(player.id)
        for _player in self.players:
            print "Player recieving ID " + str(_player.id)
            _player.protocol.transport.write(generateDataString(1, str(player.id)))

        #then send all the accepted ids to be cross referened
        for _player in self.players:
            player.protocol.transport.write(generateDataString(1, str(_player.id)))

        # add player to players
        self.players.append(player)

        # if the player is the first player in the party make it the host
        if len(self.players) == 1:
            self.host = player
            return
            
        else:
            # write a list of all the player strings to the new player
            player.protocol.transport.write(generateDataString(0, self.playerList))

    # Write player tokens to a json file
    # Call a ruby script to send the notifications
    def sendNotification(self, tokens):

        #opens the configuration file and fetches the data in it
        with open('config.json') as json_data_file:
            configData = json.load(json_data_file)

        with open(self.storageFolder + "/players.json", 'w') as outfile:
           data = {'deviceTokens' : tokens}
           json.dump(data, outfile)
  
        log.msg("Dump data and send notification")
        import subprocess
        print "ruby " + configData["pushNotificationScript"] + " -p " + str(self.port) + " -j " + self.storageFolder + "/players.json"
        subprocess.call("ruby " + configData["pushNotificationScript"] + " -p " + str(self.port) + " -j " + self.storageFolder + "/players.json", shell=True)

    # Send bet from player
    def sendBet(self, bet, betPlayer):
        self.currentBet = bet
        betString = bet.string()
        for player in self.players:
            if player != betPlayer:
                player.protocol.transport.write(generateDataString(4, betString))
        self.incrementTurn()

    # Send call from player
    def sendCall(self, callPlayer):
        for player in self.players:
            if player != callPlayer:
                player.protocol.transport.write(generateDataString(5, "CALL"))

        self.incrementTurn()

    # Send new dollars to all players
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

    # Tidy up after the round, prepare for the next
    def getRoundResult(self):

        self.round = self.round + 1
        self.bettingPlayer = None
        self.currentBet = None

        self.sendNewDollars()

    # Updates the current player
    # Checks if the round is over
    def incrementTurn(self):

        if self.players.index(self.currentPlayer) == len(self.players) - 1:
            self.currentPlayer = self.players[0]
        else:
            self.currentPlayer = self.players[self.players.index(self.currentPlayer) + 1]

        if self.bettingPlayer == self.currentPlayer:
            #the round has been played through and we can evaluate the result
            self.getRoundResult()

    # Generates an 8 digit serial number
    def generateDollar(self):
        dollar = ""
        for i in xrange(8):
            dollar += str(numpy.random.randint(10))

        return "L" + dollar + "P"

    # Begins the game
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
