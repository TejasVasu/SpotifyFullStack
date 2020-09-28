import time, json, datetime
import requests
import requests_cache
from datetime import timezone
from datetime import timedelta
import boto3, decimal

# define headers and URL
url = 'http://ws.audioscrobbler.com/2.0/'
USER_AGENT = 'Dataquest'
headers = {'user-agent': USER_AGENT}
counterCache,counterDup = 0,0 #keep track of number of times cache was utilized, and how many duplicates caught
outData = [] 

dictCache = {}
dictCounter = 0

# requests_cache.install_cache('/tmp/requests_cache') #creates a local cache in directory

def getUserCreds(user,inFile):
    inData = json.load(open(inFile))
    for ind,d in enumerate(inData):
        if d['credsName'].lower() == user.lower():
            return inData[ind]

def getNumberPages(payload, API_KEY, username):
    payload['api_key'] = API_KEY
    payload['user'] = username
    payload['format'] = 'json'
    response = requests.get(url, headers=headers, params=payload)
    respCode = response.status_code
    if respCode == 200:
        return response.json()['recenttracks']['@attr']['totalPages'], respCode
    else: # If status code is not 200, return json response as first param
        return response.json(), response 

def getRecentlyPlayed(payload, API_KEY, username,inFile,pgNum):
    # Add API key and format to the payload - need to add other pages
    payload['api_key'] = API_KEY
    payload['user'] = username
    payload['format'] = 'json'
    payload['page'] = str(pgNum)

    response = requests.get(url, headers=headers, params=payload)
    with open(inFile,'w') as outfile:
        json.dump(response.json(),outfile,indent=4)

def getTopGenreTags(payload,API_KEY):
    global counterCache
    global dictCache
    global dictCounter
    payload['method'] = 'artist.getTopTags'
    payload['api_key'] = API_KEY
    payload['format'] = 'json'

    artist = payload['artist']
    if artist in dictCache:
        tags = dictCache[artist]
        dictCounter += 1
    else:
        response = requests.get(url, headers=headers, params=payload)
        tags = [t['name'] for t in response.json()['toptags']['tag'][:3]]
        dictCache[artist] = tags

    # response = requests.get(url, headers=headers, params=payload)
    # if response.from_cache: #implementing caching
    #     counterCache += 1
    # else:
    #     time.sleep(0.15) #To ensure rate limiting
    # tags = [t['name'] for t in response.json()['toptags']['tag'][:3]]

    if payload['artist'].lower() in tags: #remove occuernces of artist name if exist
        tags.remove(payload['artist'].lower()) 
    # print(tags)
    return ', '.join(tags)

def lastfm_get_track_duration(payload,API_KEY):
    payload['method'] = 'track.getinfo'
    payload['api_key'] = API_KEY
    payload['format'] = 'json'
    response = requests.get(url, headers=headers, params=payload)
    obj = response.json()['track']['duration']
    fin = int(int(obj) * 0.001) #to convert to seconds
    return fin 

def outputToFile(fileName):
    with open(fileName,'w') as outfile:
        json.dump(outData,outfile,indent=4)

def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def dateStrip(dt):
    your_dt = datetime.datetime.fromtimestamp(int(dt))
    return your_dt.strftime("%Y-%m-%d"), your_dt.strftime("%H:%M:%S")   

def dateDiff(dt,dt1):
    your_dt = datetime.datetime.fromtimestamp(int(dt))
    your_dt1 = datetime.datetime.fromtimestamp(int(dt1))
    fin_dt = your_dt - your_dt1
    return int(fin_dt.total_seconds())

def getTimeOfDay(dt):
    # Morning (0-12), Afternoon (12-5), Evening (5-9), Night (9-12)
    your_dt = datetime.datetime.fromtimestamp(int(dt))
    hour = int(your_dt.strftime("%H"))
    if hour >= 0 and hour < 12:
        return("Morning")
    elif hour >= 12 and hour < 17:
        return("Afternoon")
    elif hour >= 17 and hour < 21:
        return("Evening")
    else:
        return("Night")

def cleanseAndWrite(inFile, outputFile,API_KEY):
    inData = json.load(open(inFile))
    global outData
    global counterDup
    trName = inData['recenttracks']['track'][1]['name']
    print(trName)
    arName = inData['recenttracks']['track'][1]['artist']['#text']
    dur = lastfm_get_track_duration({
        'artist': arName,
        'track': trName
    },API_KEY)
    prevTime = "hi" 
    # Ignore, first record as it could have currently playing, which doesn't have time
    prevDt = 0
    for ind, d in enumerate(inData['recenttracks']['track'][1:]):       
        each = {}
        each['SongName'] = (d['name']).strip() #get Track Name
        each['Artist'] = (d['artist']['#text']) #get Artist name
        each['Album'] = (d['album']['#text']) #get Album Name
        dt,time = dateStrip(d['date']['uts'])
        each['ArtistTopTags'] = getTopGenreTags({'artist': d['artist']['#text']},API_KEY)
        each['Date'] = dt # get date
        each['Time'] = time #get time
        each['TimeOfDay'] = getTimeOfDay(d['date']['uts'])
        # 1st Song - duration from api, get duration from diff in time, if greater than 500
        # (signifies song was paused) assign duration to 300, & some songs don't have that info 
        if(ind == 0):
            if dur == 0:   dur = 300
            each['durationSec'] = dur
            prevDt = d['date']['uts']
        else:
            duration = dateDiff(prevDt,d['date']['uts'])
            if(duration > 500):
                duration = lastfm_get_track_duration({
                    'artist': d['artist']['#text'],
                    'track': d['name']},API_KEY)
            if duration == 0:   duration = 300
            prevDt = d['date']['uts']
            each['durationSec'] = duration
        if prevTime != time: # This handles duplicate records having same timestamp (preventing upload to dynamo)
            outData.append(each)
            prevTime = time
        else:
            counterDup += 1

# Returns previous day time range, so that batch can be run next day
def getTodayTimestampRnge():
    test = datetime.datetime.today()
    print(test)
    print(datetime.datetime(test.year,test.month,test.day) + timedelta(hours=7))
    # Account for time zone, PST -> UTC (7hrs diff)
    start = datetime.datetime(test.year,test.month,test.day) + timedelta(hours=7) - timedelta(days=1)
    finStart = (start - datetime.datetime(1970,1,1)).total_seconds()
    end = start + timedelta(days=1)
    finEnd = (end - datetime.datetime(1970,1,1)).total_seconds()
    print("Start Dates: " + str(start)+ "  -- End Date: " +str(end))
    return int(finStart), int(finEnd) #has to be in INT for api call
    
def populateTbl(dynamodb,dbTblName):
    global outData
    table = dynamodb.Table(dbTblName)
    print("Table Status: " + table.table_status)
    # with open(fileIn) as json_file:
    #     songs = json.load(json_file, parse_float=Decimal)
    # Batch write all the songs, this speeds up process
    with table.batch_writer() as batch:
        for song in outData:
            SongName = song['SongName']
            Artist = song['Artist']
            Album = song['Album']
            ArtistTopTags = song['ArtistTopTags']
            Date = song['Date']
            Time = song['Time']
            TimeOfDay = song['TimeOfDay']
            durationSec = int(song['durationSec'])
            batch.put_item(Item=song)

def lambda_handler(event, context):
    # Which user credentials to use
    print("Fetching User API Credentials")
    user = getUserCreds('TeJas','loginCreds.json')
    start, end = getTodayTimestampRnge()

    #Edit date range here
    numPages,status =  getNumberPages({'method': 'user.getrecenttracks','from': start,'to':end},user['API_KEY'],user['username'])
    
    if status == 200:
        for x in range(1,int(numPages)+1):
            print("Processing page number: "+str(x))
            #Edit date range here
            getRecentlyPlayed({'method': 'user.getrecenttracks','from': start,'to':end
            },user['API_KEY'],user['username'],user['inFile'],x)
            cleanseAndWrite(user['inFile'],user['outFile'],user['API_KEY'])
        # outputToFile(user['outFile'])
        print("No.of calls to artist tags cache: " + str(counterCache)) 
        print("Duplicates Handeled: " + str(counterDup))
    else:
        jprint(numPages)
    
    dbTblName = 'spotifyTbl'
    dynamodb = boto3.resource('dynamodb')
    populateTbl(dynamodb,dbTblName)


