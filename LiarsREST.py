from flask import Flask
from flask_restful import Resource, Api
import MySQLdb
import os
from random import randint
from ConfigParser import SafeConfigParser
import json

db = MySQLdb.connect(host="wtobeyinstance.cbepqaptqsog.us-west-1.rds.amazonaws.com",    # your host, usually localhost
                     user="wtobey",         # your username
                     passwd="eighTnine9one!",  # your password
                     db="Users")        # name of the data base

cur = db.cursor()

app = Flask(__name__)
api = Api(app)

def generateRandomString():
    letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    stringToReturn = ""
    while len(stringToReturn) != 26:
        stringToReturn += letters[randint(0, 25)]
    return stringToReturn

@app.route('/print', methods=['GET'])
def shutdown():
    return 'Test Print'

class Game(Resource):
    def get(self):

        def get_open_port():
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("",0))
                s.listen(1)
                port = s.getsockname()[1]
                s.close()
                return port

        newFolder = "GAME_" + generateRandomString()

        with open('config.json') as json_data_file:
            data = json.load(json_data_file)

        pidfile = newFolder + "/pidfile.pid"
        logfile = newFolder + "/logfile.log"

        import subprocess
        origWD = os.getcwd() # remember our original working directory
        print origWD
        os.chdir(data['storageFolder'])
        os.mkdir(newFolder)
        port = get_open_port()
        folder = data['storageFolder'] + "/" + newFolder
        subprocessCall = "twistd " + "--pidfile " + pidfile + " --logfile " + logfile + " liars -p " + str(port) + " -s " + folder
        print subprocessCall
        print subprocess.check_output(subprocessCall, shell=True)
        subprocess.call("touch " + newFolder + "/players.json", shell=True)
        os.chdir(origWD)
        return {"port":port}

class User(Resource):
    def post(self):
        return {'status': 'success'}

api.add_resource(Game, '/Game')

if __name__ == '__main__':
    app.run(debug=True)
