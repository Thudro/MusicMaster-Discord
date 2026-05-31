from os import environ
import asyncio
from pypresence import Presence
from pypresence.types import ActivityType
import time
import requests

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager

cachedArtist = None
cachedTitle = None

#This helped a lot, just changing the winrt to winsdk 
#https://github.com/curtisgibby/winrt-slack-python/blob/master/winrt-track-change-to-slack.py#L177-L183

async def get_media_info():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:  # there needs to be a media session running
        info = await current_session.try_get_media_properties_async()

        return info.title, info.artist
    else:
        return None, None

def fetch_album_art(song_details):
    print("[MusicMaster Debug]: Getting image from iTunes")
    # Url dosnt like spaces
    query = song_details.replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # Ensure something is there
        if data["resultCount"] > 0:
            artwork_url = data["results"][0]["artworkUrl100"]

            #Increase resolution to fit pannel
            artwork_url = artwork_url.replace("100x100", "600x600")
            return artwork_url
        else:
            return None
    else:
        return None

def main():
    title, artist = asyncio.run(get_media_info())

    if not title or not artist:
        print("[MusicMaster Debug]: No media session found, clearing RPC")
        rpc.clear()
        return
    
    print("[MusicMaster Debug]: WinSDK info retrived")

    global cachedTitle, cachedArtist

    if title == cachedTitle and artist == cachedArtist:
            print("[MusicMaster Debug]: No change in song, skipping RPC update")
            return

    rpc.update(
        name=(title + " - " + artist)[:128], # Discord has a 128 character limit for the name field, so trim it if it's too long
        details=title,
        state= artist,
        large_image= fetch_album_art(title + " " + artist),
        start=1,
        end=1,
        activity_type=ActivityType.LISTENING
    )

    print("[MusicMaster Debug]: Discord RPC Updated")

    cachedTitle = title
    cachedArtist = artist

if __name__ == '__main__':
    #RPC connection only needs to be made once. 
    client_id = environ.get('DRP_ID')  # https://discord.com/developers/applications
    rpc = Presence(client_id)
    rpc.connect()

    print("[MusicMaster Debug]: Discord RPC connected")

    while True:
        main()
        time.sleep(10)
