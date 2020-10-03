Statify
=======

Fetch your Spotify data (playlists and listenings) and add it to a Sqlite database. See [examples of queries](https://github.com/foobuzz/statify/blob/master/queries.sql) you can then run on this database.


## Installation

 1. Install the Python package:

```
pip install statify
```

 2. Create your own [Spotify App](https://developer.spotify.com/dashboard/applications) and configure its credential in the statify config file (`~/.config/statify.yaml`):

```
spotify_app:
  client_id: your_app_id
  client_secret: your_app_secret
```

 3. Authorize yourself on your App:

```
statify auth [--headless]
```

By default the `auth` command will open the default browser and ask you to consent to Statify fetching your playlists and listenings. If you're installing Statify on a headless machine (e.g. Raspberry Pi on SSH), then you need to use the `--headless` option so that instead of opening the default browser, a URL is printed to stdout, and you're responsible to visit it and then paste the URL you're redirected to.


## Usage

Update the database with the state of all your playlists:

	statify pull playlists

Update the database with your latest listenings:

	statify pull listenings
	Match previous listenings fetch at 2020-07-04T16:17:54.247Z
	Added 21 listenings. Newest played_at is now 2020-07-05T08:52:10.641Z

The Spotify API only gives access to the latest 100 listenings, so you should run the last command as a cron regular enough not to have holes in your listenings history.

You can also update everything (playlists and listenings):

	statify pull


## FAQ

**Why do I need to create an App on Spotify and authorize myself on it?**

Spotify has no "private app" or "script app" mechanism that would allow individual users to use the Spotify API on their own account. So the only way to consumme the Spotify API as a given user is to create an App with OAuth 2.0 authorization and authorize oneself on it.

Statify could have been a website running a single App and fetching data about multiple users having authorized it, but as a developer I don't want to maintain such service, and as a user you shouldn't have your data be handed to a third-party in order to get it.


**What about data exports?**

Spotify allows users to export their data [from there](https://www.spotify.com/ca-en/account/privacy/). Such data exports don't contain the entire history but only one year of history, which is still better than Statify which can only grab data from the moment it is intalled as a cron. However, Statify has the following advantages over such data export:

 - The data export needs to be ordered manually from the Spotify web interface and will take a few days to generate (at which point Spotify sends you an email). In comparison, a single `statify pull` automatically fetches your data.
 - Once you've ordered one data export, it is cached and you cannot order a second one for some time (I don't how much time, since I'm still having my own one cached, and that has been 12 days) meaning you'll need to wait in order to have your data up-to-date. In comparison, assuming you run `statify pull` in a cron, your Statify database is always up-to-date.
 - The data in the data export (in JSON) is way less rich than the data from the Spotify API. Most notably, listenings in the export don't have the Spotify ID of songs listened to, meaning the only way to retrieve the associated rich data from the API would be via a Search, which would not be very reliable.
 - More generally, the data export is in a badly documented format that could be easily broken or updated according to Spotify's internal decisions. The API is well-documented and can be considered stable on a given version.

Here is an example of a listening in the data export from June 2020:

	{
		"endTime" : "2020-05-04 17:17",
		"artistName" : "French 79",
		"trackName" : "Diamond Veins (feat. Sarah Rebecca)",
		"msPlayed" : 3822
	}

Here is an example of a listening in the Statify database (the relational format is denormalized here in JSON for consistency):

	{
		"track": {
			"id": "5G0oVoL309pqsvGDzhMOwx",
			"web_url": "https://open.spotify.com/track/5G0oVoL309pqsvGDzhMOwx",
			"name": "Diamond Veins (feat. Sarah Rebecca)",
			"cover_url": "https://i.scdn.co/image/ab67616d0000b2732cda1a639cd6e26ccfc0773b",
			"preview_url": "https://p.scdn.co/mp3-preview/c904f3f3a098bd88cb3359c0c3605dcf0f5b3225",
			"duration": 240120,
			"explicit": 0,
			"iscr": "FR9W11161070",
			"popularity": 58,
			"album": {
				"id": "6rkKOTP3oBns0nR6mfHOsH",
				"web_url": "https://open.spotify.com/album/6rkKOTP3oBns0nR6mfHOsH",
				"cover_url": "https://i.scdn.co/image/ab67616d0000b2732cda1a639cd6e26ccfc0773b",
				"name": "Olympic",
				"release_date": "2016-10-21"
			},
			"artists": [
				{
					"id": "6MJKlN8ya42Agsw3iQZs6e",
					"web_url": "https://open.spotify.com/artist/6MJKlN8ya42Agsw3iQZs6e",
					"name": "French 79"
				}
			]
		},
		"played_at": "2020-05-04T17:17:18.254Z",
		"context": {
			"type": "playlist",
			"playlist": {
				"spotify_id": "56DcZmigEBatLaDqswNKOx",
				"web_url": "https://open.spotify.com/playlist/56DcZmigEBatLaDqswNKOx",
				"cover_url": "https://mosaic.scdn.co/640/coverurl",
				"name": "Electro",
				"is_public": false,
				"owner_name": "Valentin"
			}
		}
	}

The rich data from the API that Statify grabs would allow the implementation of a "Year in review" webpage in the likes Spotify has been doing for 2019, with only front-end work (I would definitely merge that, if you feel inspired).
