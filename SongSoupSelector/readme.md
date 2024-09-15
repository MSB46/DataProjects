# SongSmoothieSoup - A Custom Song Recommendation System

### About
An application that provides a list of similar songs based on a user's own selection of songs. I made this application to practice my knowledge in recommendation systems and API utilization, but you are free to try this application for yourself if you'd like. Below are the steps I'd take if you're curious.

![Step 0](./preview.jpeg "Application preview")

### Demo
1) Determine whether you're entering the name of a song or artist.

![Step 1](./step1.jpeg "Searching a song or artist")

2) Clicking on 'Search' provides a selection of songs associated with what you typed.

![Step 2](./step2.jpeg "Selection of songs associated with typed song or artist")

3) Click on the row number of the song that you want to add to your selection and confirm.

![Step 3](./step3.jpeg "Confirming selected song")

4) Add up to 10 songs in a selection. **Adding more songs might lead to a more volatile recommendation** but if that's your thing, feel free to experiment

![Step 4](./step4.jpeg "Adding more songs to the \"soup\"")

5) Once all songs are in the selection, click on the button labeled 'Recommend Songs'

![Step 5](./step5.jpeg "Getting songs similar to the ones you've added to the soup")

#### Spotify API implementation to add songs as a playlist.
At this point you can manually search up or add these songs to your spotify playlist but if you want a more automated approach of adding songs, you'll need a few additional things.
    * A Spotify account (Any plan should work)
    * A Spotify Developer account

a. Go to developer.spotify.com and log into your account
b. Go to your dashboard and click the button labeled "Create app"
c. The specifics of this new app isn't too important and you don't need a website. For the redirect URI, the placeholder example.com works fine. Leave the API options unchecked
d. Go to settings and keep in mind the client id and client secret. You'll need both for spotify's authentication.
e. Go to SSSoup's settings and copy and paste the client and secret ids into their respective spots.
f. Go through steps 1-7 as normal and confirm at the end. You'll be asked to login and/or confirm your account to use this application.

That should be it.

### Explorations and caveats
* When using Spotipy to automatically add songs into one of your Spotify playlists, some songs might not make it despite being displayed on a table. This is due to Spotify's ability to add and remove songs at their will and is outside this application's control.

* The full selection of songs used for this applications only represents a subset of songs that are available in Spotify's full catalog. If you would like to add a song of your own into the selection. You are more than welcome to modify dataset.csv and utilize Spotify's API to search and add the new song's metrics manually.

### Credits
Development/Documentation: MSB46

The dataset I utilized was created by a combination of datasets and code from the following sources:

* https://www.kaggle.com/code/vatsalmavani/music-recommendation-system-using-spotify-dataset/notebook

* https://towardsdatascience.com/how-to-build-an-amazing-music-recommendation-system-4cce2719a572

* https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset/

* https://www.kaggle.com/datasets/rodolfofigueroa/spotify-12m-songs/
