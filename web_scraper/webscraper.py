import requests
import json
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

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

def extract_videos_from_youtube_channel(api_key_path, json_save_path, channel_id, channel_name = ''):
    channel_videos_extractor = ExtractVideosFromChannel(channel_id, channel_name)
    channel_videos_extractor.load_api_key(api_key_path)
    channel_videos_extractor.run_video_extraction()
    channel_videos_extractor.save_extracted_videos(json_save_path)


if __name__ == '__main__':
    API_KEY = 'web_scraper/api_key.txt'
    JSON_SAVE = 'web_scraper/videos_info.json'

    CHANNEL_ID = 'UCisLo7aylCwtpF0QjnyCDPA'
    CHANNEL_NAME = 'Anime Pro - Anime on Piano'

    # NOTE: Set to True to extract and save videos from a Youtube channel
    EXTRACT_VIDEOS = False
    
    if EXTRACT_VIDEOS:
        extract_videos_from_youtube_channel(API_KEY, JSON_SAVE, CHANNEL_ID, CHANNEL_NAME)
