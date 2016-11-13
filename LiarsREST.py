from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import MySQLdb
import os
from random import randint
from ConfigParser import SafeConfigParser
import json
import MySQLdb.cursors


app = Flask(__name__)
api = Api(app)

databasename = "liarsdb.cbepqaptqsog.us-west-1.rds.amazonaws.com"
sqlUsername = "wtobey"
_db = "Users"

@app.route('/newGame', methods = ['GET'])
def newGame():

    db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                         user=sqlUsername,         # your username
                         passwd="eighTnine9one!",  # your password
                         db=_db)        # name of the data base

    cur = db.cursor()

    def get_open_port():
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("",0))
            s.listen(1)
            port = s.getsockname()[1]
            s.close()
            return port

    def generateRandomString():
        letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        stringToReturn = ""
        while len(stringToReturn) != 26:
            stringToReturn += letters[randint(0, 25)]
        return stringToReturn

    newFolder = "GAME_" + generateRandomString()

    with open('config.json') as json_data_file:
        data = json.load(json_data_file)

    pidfile = data['storageFolder'] + "/" + newFolder + "/pidfile.pid"
    logfile = data['storageFolder'] + "/" + newFolder + "/logfile.log"

    import subprocess
    origWD = os.getcwd() # remember our original working directory
    os.chdir(data['storageFolder'])
    os.mkdir(newFolder)
    port = get_open_port()
    folder = data['storageFolder'] + "/" + newFolder
    os.chdir('/home/wtobey/liars_poker')
    subprocessCall = "twistd " + "--pidfile " + pidfile + " --logfile " + logfile + " liars -p " + str(port) + " -s " + folder
    print subprocessCall
    
    print subprocess.check_output(subprocessCall, shell=True)
    subprocess.call("touch " + newFolder + "/players.json", shell=True)
    os.chdir(origWD)

    message = {
        'status': 0,
        'message': port
    }

    resp = jsonify(message)
    resp.status_code = 0
    return resp

@app.route('/fetchUser', methods = ['GET'])
def getUser():

    #EX: curl -X GET -d 'id=26' 127.0.0.1:10000/getUser

    db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                         user=sqlUsername,         # your username
                         passwd="eighTnine9one!",  # your password
                         db=_db)        # name of the data base

    cur = db.cursor()

    userid = request.form.get('id', None)

    if userid is None:
        message = {
            'status': 1,
            'message': 'Must provide an id'
        }
        resp = jsonify(message)
        resp.status_code = 1
        return resp

    cur.execute("SELECT * FROM Users WHERE id = %s", (userid, ))
    message = {
        'status': 0,
        'message': cur.fetchone()
    }
    resp = jsonify(message)
    resp.status_code = 0
    return resp

@app.route('/testConnectivity')
def returnTrue():
    message = {
        'status': 0,
        'message': 'Success'
    }
    resp = jsonify(message)
    resp.status_code = 0
    return resp

@app.route('/newUser/<token>')
def addUser(token):

    db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                         user=sqlUsername,         # your username
                         passwd="eighTnine9one!",  # your password
                         db=_db)        # name of the data base

    cur = db.cursor()

    print "NewUser"
    print token

    if token is None:
        message = {
            'status': 1,
            'message': 'Must provide a token'
        }
        print "Token not provided"
        resp = jsonify(message)
        resp.status_code = 1
        return resp

    cur.execute("INSERT INTO Users (device_token) VALUES (%s)", (token, ))
    db.commit()
    cur.execute("SELECT id FROM Users WHERE device_token = %s", (token, ))
    message = {
        'status': 0,
        'message': cur.fetchone()[0]
    }
    resp = jsonify(message)
    resp.status_code = 0
    return resp

@app.route('/searchUser/<searchString>')
def searchUser(searchString):

    db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                         user=sqlUsername,         # your username
                         passwd="eighTnine9one!",  # your password
                         db=_db,
                         cursorclass=MySQLdb.cursors.DictCursor)        # name of the data base

    cur = db.cursor()

    count = 0
    needNewString = True

    # return no result until a third character is entered
    if len(searchString) < 3:
        message = {
            'status': 0,
            'message': {}
        }

        resp = jsonify(message)
        resp.status_code = 0
        return resp

    #tracks the length of the string to remove the trailing comma for the last value
    stringIndex = 0

    #holds the match against string
    masterMatchString = ""

    for letter in searchString:

        stringIndex += 1

        if letter == " ":
            #dont process a space, just continue and let the loop know a new word is needed
            needNewString = True
            continue
        if needNewString:
            #reset word
            word = ""
            #set new string to false until we get a space
            needNewString = False

        #add one to count, which tracks the total number of statements
        count += 1
        #add the letter to word
        word += letter

        #get the score value for the relevance grade
        score = "score" + str(count)

        if stringIndex != len(searchString):
            matchString = "MATCH (username, name) AGAINST ('" + word + "*' " + "IN BOOLEAN MODE) AS " + score + ","
        else:
            matchString = "MATCH (username, name) AGAINST ('" + word + "*' " + "IN BOOLEAN MODE) AS " + score

        masterMatchString += matchString + "\n"

    #holds the string of scoreX + scoreY...
    additionString = ""
    #counts up to count
    count2 = 0

    while count2 < count:

        count2 += 1

        if count2 == count:
            additionString += "score" + str(count2)
        else:
            additionString += "score" + str(count2) + " + "

    cur.execute("SELECT name, username, id, device_token, " + masterMatchString + " FROM Users HAVING " + additionString + " > 0.1 " + "ORDER BY " + additionString + " DESC")
    message = {
        'status': 0,
        'message': cur.fetchall()
    }

    resp = jsonify(message)
    resp.status_code = 0
    return resp

@app.route('/user', methods = ['PUT', 'POST'])
def updateUser():

    db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                         user=sqlUsername,         # your username
                         passwd="eighTnine9one!",  # your password
                         db=_db)        # name of the data base

    cur = db.cursor()

    if request.method == 'PUT':
        print "put"


    else:

        #EX: curl -X POST -d 'id=26&username=WillToblerone' 127.0.0.1:10000/newUser
        print 'POST'
        print request.form
        id = request.form.get('id', None)
        username = request.form.get('username', None)
        token = request.form.get('token', None)
        name = request.form.get('name', None)

        if id is None or (username is None and token is None and name is None):
            message = {
                'status': 1,
                'message': 'Must provide an id and either a username or a token'
            }
            resp = jsonify(message)
            resp.status_code = 1
            return resp

        if not username is None:
            cur.execute("UPDATE Users SET username=%s WHERE id=%s", (username, id))
            db.commit()

        if not token is None:
            cur.execute("UPDATE Users SET token=%s WHERE id=%s", (token, id))
            db.commit()

        if not name is None:
            cur.execute("UPDATE Users SET name=%s WHERE id=%s", (name, id))
            db.commit()

        message = {
            'status': 0,
            'message': 'Success'
        }
        resp = jsonify(message)
        resp.status_code = 0
        return resp

if __name__ == '__main__':
    app.run(debug=True)
