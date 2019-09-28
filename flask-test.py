import flask, redis, time, threading

from flask import jsonify, request

r = redis.Redis(host='localhost', port=6379, db=0)

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/messages/sent/', methods=['GET', 'POST'])
def sendMessage():
    username = request.form['username']
    message = request.form['message']
    room = request.form['roomname']
    value = {
        "username": username,
        "message": message
    }
    roomname = "room:" + room
    r.xadd(roomname, value)
    r.zincrby("leaderboard", 1, username)
    return '1'


@app.route('/messages/readLast/<roomname>', methods=['GET', 'POST'])
def readLastMessage(roomname):
    roomname = "room:" + roomname
    value = {
        roomname: "0-0"
    }
    readdata = r.xread(value)
    streamLength = len(readdata[0][1])
    lastmessagedict = {}
    messagesDict = {}
 # pojedyncza wiadomosc
    lastmessagedict = readdata[0][1][streamLength-1][1]
    decoded = {k.decode('utf8'): v.decode('utf8') for k, v in lastmessagedict.items()}
    return jsonify(decoded)


@app.route('/messages/readAll/<roomname>', methods=['GET'])
def readAllMessages(roomname):
    roomname = "room:" + roomname
    value = {
        roomname: "0-0"
    }
    readdata = r.xread(value)
    streamLength = len(readdata[0][1])
    lastmessagedict = {}
    messagesDict = {}
    messagesDict2 = {}
    messagesList = []
    # wszyskie wiadomosci
    x = 0
    for x in range(streamLength):
        lastmessagedict = readdata[0][1][x][1]
        decoded = {k.decode('utf8'): v.decode('utf8') for k, v in lastmessagedict.items()}
        messagesList.append(decoded)
    
    messagesDict2['messages'] = messagesList
    return jsonify(messagesDict2)     


@app.route('/leaderboard/', methods=['GET'])
def displayLeaderboard():
    readdata = r.zrevrange("leaderboard", 0, -1, withscores = True)
    leaderboardDict = {}
    leaderboardList = []
    x = 0
    for x in range(len(readdata)):
        leaderboardList.append({ 'userName' : readdata[x][0].decode('utf8'), 'score' : readdata[x][1] })
  #      leaderboardDict[x] = { 'userName' : readdata[x][0].decode('utf8'), 'score' : readdata[x][1] }

    leaderboardDict['leaderboard'] = leaderboardList
    return jsonify(leaderboardDict)


StartTime=time.time()


class setInterval :
    def __init__(self,interval,action) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()


def dumpDatabase():
    save = r.bgsave()
    return save


inter = setInterval(30,dumpDatabase)
app.run()
