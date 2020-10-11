# SpotifyFullStack
Full Stack project sourcing data from Spotify through last.fm, hosted on AWS

## Installations Required
*	Install Homebrew
*	Install Pyenv (Optional)(python version management). Use python version 3 for this project
*	pip install requests-cache

## Setup Last.FM
* Create Last.Fm account https://secure.last.fm/login
* Go to: Settings -> Applications -> Connect for both Spotify scrobbling/playback
* Create API account https://www.last.fm/api/account/create. Just full in Application name, Application description, leave last 2 blank.
* Store Credentials

## Setup login creds file (required)
Create a json file "loginCreds.json" and enter in the following information, replace the () fields with your info
```
[
    {
        "credsName": "(any name you want)",
        "inFile" : "(enter desired file name).json",
        "outFile" : "(enter desired file name).json",
        "username" : "(lastfm username)",
        "API_KEY" : "(lastfm api key)"
    } (insert comma, followed by more users you would like to have)
]
```
Once this is done, in the main function of lastfm.py, update the getUserCreds() function to your credsName

## Running file
* Json files are automatically created when project is run
* python lastfm.py -> this obtains recent tracks from lastfm.api, cleans/adds data and dumps a json file
* python analyzeData.py -> this goes through json output and creates metrics.

### Notes
* Install/implement caching (for getting artist tags) https://pypi.org/project/requests-cache/

### Reference Websites
* https://blog.miguelgrinberg.com/post/how-to-create-a-react--flask-project
#### LastFM
* https://www.jayblanco.com/blog/2016/7/9/using-lastfm-and-r-to-understand-my-music-listening-habits
* https://github.com/encukou/lastscrape-gui/blob/master/lastexport.py
* https://www.last.fm/api/show/user.getPersonalTags
* https://www.dataquest.io/blog/last-fm-api-python/

