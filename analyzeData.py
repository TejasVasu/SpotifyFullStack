import time, json, datetime
from datetime import date
from collections import Counter

songCount, numGenreTags, morning, noon, evening, night = 0,0,0,0,0,0
morningDur, noonDur, eveningDur, nightDur = 0,0,0,0
outData = {}
topGenreDict = {}

def getUserCreds(user,inFile):
    inData = json.load(open(inFile))
    for ind,d in enumerate(inData):
        if d['credsName'].lower() == user.lower():
            return inData[ind]

def outputToFile(fileName):
    with open(fileName,'w') as outfile:
        json.dump(outData,outfile,indent=4)

def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def usageThroughDay(timeOfDay,duration):
    global morning, noon, evening, night
    global morningDur, noonDur, eveningDur, nightDur
    if timeOfDay == 'Morning': 
        morning += 1
        morningDur += duration
    elif timeOfDay == 'Afternoon': 
        noon += 1
        noonDur += duration
    elif timeOfDay == 'Evening': 
        evening += 1
        eveningDur += duration
    else: 
        night += 1
        nightDur += duration

# Unpacks 0-3 genre tags per song entry, and put into dict
def getTopGenres(input):
    global numGenreTags
    if len(input) != 0:
        stripped = input.split(",")
        numGenreTags += len(stripped)
        for tag in stripped:
            finTag = tag.strip()
            topGenreDict[finTag] = topGenreDict.get(finTag,0) + 1
    
def showUsageMetric(count):
    print("Songs Throughout the day")
    morningDurMin, noonDurMin, eveningDurMin, nightDurMin = int(morningDur/60), int(noonDur/60), int(eveningDur/60), int(nightDur/60)
    usage= {}
    numSong = {"Morning": morning, "Afternoon": noon, "Evening": evening, "Night": night}
    usage['numberOfSongs'] = numSong
    durOfSongs = {"Morning": morningDurMin, "Afternoon": noonDurMin, "Evening": eveningDurMin, "Night": nightDurMin}
    usage['durationOfSongs'] = durOfSongs
    usage['totalMins'] = morningDurMin + noonDurMin + eveningDurMin + nightDurMin
    usage['totalSongs'] = count
    return usage

# Parse through counter object and converts to dict object
# Parameters (input dictionary, metric name, number of entries to display)
def writeCounterOutput(inDict,metric,num):
    global outData
    inList = Counter(inDict).most_common(num)
    eachItem = {}
    for ind in range(len(inList)):
        eachItem[str(inList[ind][0])] = inList[ind][1]
    outData[metric] = eachItem

def analyzeFile(inFile,currentDate):
    global songCount
    global outData
    global topGenreDict
    global numGenreTags
    artistDict = {}
    trackDict = {}
    inData = json.load(open(inFile))
    for ind, d in enumerate(inData):
        # if d['Date'] == currentDate: #In order to only process current date's
        #     counter += 1
        # else:
        #     break
        songCount += 1
        usageThroughDay(d['TimeOfDay'],d['durationSec'])
        artistDict[d['Artist']] = artistDict.get(d['Artist'],0) + 1
        trackDict[d['SongName']] = trackDict.get(d['SongName'],0) + 1
        getTopGenres(d['ArtistTopTags'])

    usage = showUsageMetric(songCount)
    outData['usageStats'] = usage
    writeCounterOutput(artistDict,"topArtists",5)
    writeCounterOutput(trackDict,"topTracks",4)
    writeCounterOutput(topGenreDict,"topGenreTags",5)
    outData['totalGenreTags'] = numGenreTags


if __name__ == "__main__":
    print("Running Data Analyzer")
    print("Fetching User API Credentials")
    user = getUserCreds('TeJas','loginCreds.json')

    print("Analyzing File..")
    curDate = date.today().strftime("%Y-%m-%d") #Passing in current date
    analyzeFile(user['outFile'],curDate)
    outputToFile('finalMetrics.json')
    
    