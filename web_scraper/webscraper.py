import os
import json
import requests

from bs4 import BeautifulSoup
from googleapiclient.discovery import build

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

class ExtractVideosFromChannel:
    """Extracts all Videos from a Youtube Channel using the Youtube API (v3)."""
    youtube_api_service_name = 'youtube'
    youtube_api_version = 'v3'

    def __init__(self, channel_id, channel_name = ''):
        self.api_key = ''

        self.channel_name = channel_name
        self.channel_id = channel_id

        self.youtube_resource = None

        self.videos = {
            'channel_name': self.channel_name,
            'channel_id': self.channel_id,
            'videos': []
        }
    
    # Loads the API key to be used
    def load_api_key(self, path_to_key_file):
        with open(path_to_key_file, 'r') as api_key_file:
            self.api_key = api_key_file.read().replace('\n', '')
    
    # Stores relevant video info
    def store_video(self, video):
        video_info = {
            'id': video['snippet']['resourceId']['videoId'],
            'title': video['snippet']['title'],
            'description': video['snippet']['description']
        }
        self.videos['videos'].append(video_info)

    # Calls Youtube API to extract videos
    def run_video_extraction(self):
        # Create API resources object
        self.youtube_resource = build(
            ExtractVideosFromChannel.youtube_api_service_name,
            ExtractVideosFromChannel.youtube_api_version,
            developerKey=self.api_key)

        # Retrieve playList ID of all songs
        request = self.youtube_resource.channels().list(
            part='contentDetails',
            id=self.channel_id
        )
        response = request.execute()

        # TODO: Auto-populate youtube channel name (if empty)
        playListID = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Cycle through all videos and store relevant information
        request = self.youtube_resource.playlistItems().list(
            part='snippet',
            maxResults=50,
            playlistId=playListID
        )
        response = request.execute()

        for video in response['items']:
            self.store_video(video)
        
        while 'nextPageToken' in response:
            # Request video list
            request = self.youtube_resource.playlistItems().list(
                part='snippet',
                maxResults=50,
                pageToken=response['nextPageToken'],
                playlistId=playListID
            )
            response = request.execute()

            # Store video info
            for video in response['items']:
                self.store_video(video)

    # Saves extracted video info to a JSON file
    def save_extracted_videos(self, json_save_path):
        with open(json_save_path, 'w+') as json_file:
            json.dump(self.videos, json_file)

class MidiDownloader:
    """Downloads midi files from mediafire links found in Youtube video descriptions."""

    def __init__(self):
        self.midi_links = []
        self.download_links = []
    
    # Parses midi links from video descriptions
    def extract_midi_links(self, videos_path):
        with open(videos_path, 'r') as json_file:
            videos = json.load(json_file)

            # Cycle through all videos
            for video in videos['videos']:
                midi_link = self.parse_midi_download_link(video['description'])

                # Add existent, non-duplicate midi links
                if (midi_link != None) and (midi_link not in self.midi_links):
                    self.midi_links.append(midi_link)
    
    # NOTE: this function is highly dependent on the structure of the video's description
    def parse_midi_download_link(self, text):
        data = text.split('\n')

        # midi file link follows 'Midi:'
        if 'Midi:' in data:
            midi_link_index = data.index('Midi:') + 1
            midi_link = data[midi_link_index]

            # Will only permit midi file links from 'www.mediafire.com'
            if ('www.mediafire.com' in midi_link) and ('.mid' in midi_link):
                return midi_link
        
        # No valid midi link found
        return None
    
    # NOTE: this function is SLOW
    def webscrape_direct_download_links(self):
        for link in self.midi_links:
            # Get web page associated to midi_link
            response = requests.get(link)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract direct download link
            el = soup.find('div', attrs={'id': 'download_link'})
            el = el.find('a', attrs={'aria-label': 'Download file'})

            self.download_links.append(el['href'])

    def save_direct_download_links(self, save_path):
        with open(save_path, 'w+') as json_file:
            json.dump(self.download_links, json_file)
    
    def load_direct_download_links(self, links_path):
        with open(links_path, 'r') as json_file:
            self.download_links = json.load(json_file)
    
    # Downloads midi files to save_dir
    def download_midi_files(self, save_dir):
        for link in self.download_links:
            # Retrieve midi file
            with requests.get(link, stream=True) as file_request:
                # Extract file name
                data = link.split('/')
                name = data[-1]

                # Save midi file
                with open(save_dir + '/' + name, 'wb') as midi_file:
                    midi_file.write(file_request.content)

# Wrapper for using ExtractVideosFromChannel class
def extract_videos_from_youtube_channel(api_key_path, json_save_path, channel_id, channel_name = ''):
    channel_videos_extractor = ExtractVideosFromChannel(channel_id, channel_name)
    channel_videos_extractor.load_api_key(api_key_path)
    channel_videos_extractor.run_video_extraction()
    channel_videos_extractor.save_extracted_videos(json_save_path)

# Wrapper for using MidiDownloader class
def download_midi_file_from_videos(extract_download_links, download_midi_files, videos_path = None, links_path = None, midi_save_dir = None):
    midi_downloader = MidiDownloader()

    # Extract Direct Download Links
    if extract_download_links:
        # Need to specify video_path to extract links
        if videos_path == None:
            print('Specify a \"video_path\" when extracting download links')
            return
        
        midi_downloader.extract_midi_links(videos_path)
        midi_downloader.webscrape_direct_download_links()

        # Save Direct Download Links
        if links_path != None:
            midi_downloader.save_direct_download_links(links_path)
    
    # Download Midi Files specified by Direct Download Links
    if download_midi_files:
        # Need to specify midi_save_dir to download midi files
        if midi_save_dir == None:
            print('Specify a \"midi_save_dir\" when downloading midi files')
            return
        
        # Load Direct Download Links
        if links_path != None:
            midi_downloader.load_direct_download_links(links_path)
        
        midi_downloader.download_midi_files(midi_save_dir)


if __name__ == '__main__':
    print('\n')

    ### Variables to Customize ###

    API_KEY = DIR_PATH + '/api_key.txt'
    VIDEOS_SAVE = DIR_PATH + '/videos_info.json'
    LINKS_SAVE = DIR_PATH + '/download_links.json'
    MIDI_SAVE_DIR = os.path.dirname(DIR_PATH) + '/MIDI_Samples'

    CHANNEL_ID = 'UCisLo7aylCwtpF0QjnyCDPA'
    CHANNEL_NAME = 'Anime Pro - Anime on Piano'

    # NOTE: Set to True to extract and save videos from a Youtube channel
    EXTRACT_VIDEOS = False

    # NOTE: If False, it is assumed there exists download_links.json
    EXTRACT_DOWNLOAD_LINKS = False
    # NOTE: Set to True to download midi files from scraped videos
    DOWNLOAD_MIDI_FILES = True
    
    ### Execution ###

    if EXTRACT_VIDEOS:
        extract_videos_from_youtube_channel(API_KEY, VIDEOS_SAVE, CHANNEL_ID, CHANNEL_NAME)
    
    download_midi_file_from_videos(EXTRACT_DOWNLOAD_LINKS, DOWNLOAD_MIDI_FILES, videos_path=VIDEOS_SAVE, links_path=LINKS_SAVE, midi_save_dir=MIDI_SAVE_DIR)
