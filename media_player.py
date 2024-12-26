import os
import asyncio
import aiohttp
import logging
import datetime

from homeassistant.components.media_player import (
    MediaPlayerEntity
)
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY, SUPPORT_STOP, MEDIA_TYPE_VIDEO,
)
from homeassistant.const import STATE_IDLE, STATE_PLAYING
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the media player platform."""
    config = config_entry.data
    download_dir = config["download_dir"]
    video_urls = config["video_urls"]
    player = SolarVideoPlayer(hass, download_dir, video_urls)
    async_add_entities([player], True)

    async def async_update_videos(now):
        """Update videos on interval."""
        await player.async_download_videos()

    async_track_time_interval(hass, async_update_videos, datetime.timedelta(days=1)) #update every day

class SolarVideoPlayer(MediaPlayerEntity):
    """Representation of a Solar Video player."""

    def __init__(self, hass, download_dir, video_urls):
        self.hass = hass
        self._download_dir = download_dir
        self._video_urls = video_urls
        self._state = STATE_IDLE
        self._media_content_id = None
        self._media_content_type = MEDIA_TYPE_VIDEO
        self._attr_supported_features = SUPPORT_PLAY | SUPPORT_STOP
        self._filename = None
        self._last_download = None

    @property
    def name(self):
        return "Solar Video Player"

    @property
    def state(self):
        return self._state

    @property
    def media_content_id(self):
        return self._media_content_id

    @property
    def media_content_type(self):
        return self._media_content_type

    async def async_update(self):
        if not os.path.exists(self._download_dir):
            os.makedirs(self._download_dir, exist_ok=True)

        files = [f for f in os.listdir(self._download_dir) if f.endswith(".mp4")]
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            self._filename = files[0]
            self._media_content_id = f"/local/solar_videos/{self._filename}"
        else:
            self._media_content_id = None

    async def async_download_videos(self):
        now = datetime.datetime.now()
        if self._last_download and (now - self._last_download).total_seconds() < 86400: #86400 seconds = 1 day
             _LOGGER.info("Videos were downloaded less than a day ago, skipping.")
             return
        session = async_get_clientsession(self.hass)
        for url in self._video_urls:
            filename = os.path.basename(url)
            filepath = os.path.join(self._download_dir, filename)

            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(filepath, "wb") as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        _LOGGER.info(f"Downloaded {filename} successfully.")
                    else:
                        _LOGGER.error(f"Error downloading {url}: {response.status}")
            except aiohttp.ClientError as e:
                _LOGGER.error(f"Error downloading {url}: {e}")
            except OSError as e:
                _LOGGER.error(f"Error writing file {filename}: {e}")

        self._last_download = datetime.datetime.now() #update last download time
