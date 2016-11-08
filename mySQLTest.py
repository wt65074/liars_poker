
import MySQLdb

databasename = "127.0.0.1" #liarsdbinstance.cbepqaptqsog.us-west-1.rds.amazonaws.com:3306
sqlUsername = "root" #wtobey

db = MySQLdb.connect(host=databasename,    # your host, usually localhost
                     user=sqlUsername,         # your username
                     passwd="eighTnine9one!",  # your password
                     db="Liars")        # name of the data base

cur = db.cursor()

string = "ho"

count = 0
needNewString = True

# return no result until a third character is entered

word = ""

#tracks the length of the string to remove the trailing comma for the last value
stringIndex = 0

#holds the match against string
masterMatchString = ""

for letter in string:

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

    if stringIndex != len(string):
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

cur.execute("SELECT name, username, device_token, " + masterMatchString + " FROM Users HAVING " + additionString + " > 0.1 " + "ORDER BY " + additionString + " DESC")

print cur.fetchall()
