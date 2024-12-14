# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import inputstreamhelper
from uuid import uuid4 as make_uuid
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from time import time, strftime, strptime, localtime
from calendar import timegm

KODI_VERSION = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])

PATHS = ('main_menu', {
	'play': 'play_video',
	'movies': ('list_movies', {}),
	'series': 'show_series',
	'special': 'show_special',
	'live': ('play_live', {}),
	'settings': ('open_settings', {}),
})

COMMON_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) 6.0'}

DISCO_REALM = 'dmaxde'

DISCO_HEADERS = {
	'Accept': '*/*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Referer': 'https://tele5.de/',
	'X-disco-client': 'Alps:HyogaPlayer:0.0.0',
	'X-disco-params': 'realm='+DISCO_REALM,
	'X-Device-Info': 'STONEJS/1 (Unknown/Unknown; Unknown/Unknown; Unknown)',
	'Origin': 'https://tele5.de',
	#'Sec-Fetch-Dest': 'empty',
	#'Sec-Fetch-Mode': 'cors',
	#'Sec-Fetch-Site': 'cross-site',
	#'Sec-GPC': '1',
}

DISCO_HOST = 'https://eu1-prod.disco-api.com'
DISCO_ID = '626'

MANIFEST_TYPES = {'dash': 'mpd', 'hls': 'hls'}
DRM_API = 'widevine'
DRM_KODI = 'com.widevine.alpha'


class clientMaster():
	def __init__(self, *args, **kwargs):
		super(clientMaster, self).__init__()
		url = urlsplit(sys.argv[0])
		path = url.path.strip('/')
		self.handle = int(sys.argv[1])
		self.plugin = url.netloc
		self.addon = xbmcaddon.Addon()
		self.name = self.addon.getAddonInfo('id')
		self.version = self.addon.getAddonInfo('version')
		self.show_online = int(self.addon.getSetting('visual_remaining'))

		xbmcplugin.setContent(self.handle, 'tvshows')
		paths = PATHS
		while isinstance(paths, tuple):
			if path == "":
				getattr(self, paths[0])()
				break
			else:
				head, _, path = path.partition('/')
				paths = paths[1][head]
		else:
			getattr(self, paths)(path)

	def main_menu(self):
		item_uno = self.create_entries('DEFAULT', {'Title': self.translate(32201), 'Plot': self.translate(32202),\
			'Mediatype': 'video'}, '', self.get_thumb('livestream.png'))
		item_uno.setProperty('isPlayable', 'true')
		self.add_dir_item('/live', item_uno)
		for path, title in [('/movies', 32203), ('/series', 32204), ('/special', 32205)]:
			item_due = self.create_entries('DEFAULT', {'Title': self.translate(title)}, '', self.get_thumb('icon.png'))
			self.add_dir_item(path, item_due, True)
		if self.addon.getSetting('show_settings') == 'true':
			item_tre = self.create_entries('DEFAULT', {'Title': self.translate(32206)}, '', self.get_thumb('settings.png'))
			self.add_dir_item('/settings', item_tre)
		self.end_dir()

	def open_settings(self):
		self.addon.openSettings()
		xbmc.executebuiltin('Container.Refresh')

	def list_movies(self):
		for movie in self.fetch_disco_paginated("/content/videos?include=images,genres,show"\
			f"&filter[videoType]=STANDALONE&filter[primaryChannel.id]={DISCO_ID}"):
			for method in self.set_sort_methods(): xbmcplugin.addSortMethod(self.handle, method)
			show = movie['relationships']['show']['data']
			if show['attributes']['videoCount'] > 1 or not str(movie['attributes'].get('videoDuration')).isdecimal():
				continue
			item = self.create_entries('STREAM', movie, 'movie')
			self.add_dir_item(f"/play/{movie['id']}", item)
		self.end_dir()

	def show_series(self, series_id):
		if not series_id:
			return self.list_series()
		series_id, _, season = series_id.partition('/')
		season_filter = f"&filter[seasonNumber]={season}" if season else ""
		videos = list(self.fetch_disco_paginated("/content/videos"\
			f"?include=images,show&filter[show.id]={series_id}{season_filter}"))
		if not videos:
			return
		show_title = videos[0]['relationships']['show']['data']['attributes']['name']
		if len(videos) > 7:
			seasons = set(video['attributes']['seasonNumber'] for video in videos)
			if len(seasons) > 1:
				for season in sorted(seasons):
					item_uno = self.create_entries('OTHERS', {'Title': f"Staffel {str(season)}", 'TvShowTitle': show_title,\
						'Season': season, 'Mediatype': 'season'}, '', self.get_thumb('standard.png'))
					self.add_dir_item(f"/series/{series_id}/{season}", item_uno, True)
				self.end_dir()
		episodes = []
		for video in videos:
			if video['attributes']['videoType'] == 'EPISODE':
				episodes.append(video)
			else:
				if not str(video['attributes'].get('videoDuration')).isdecimal():
					continue
				item_due = self.create_entries('STREAM', video, 'video')
				self.add_dir_item(f"/play/{video['id']}", item_due)
		episodes.sort(key=lambda v: (v['attributes']['seasonNumber'], v['attributes']['episodeNumber']))
		for episode in episodes:
			if not str(episode['attributes'].get('videoDuration')).isdecimal():
				continue
			shorts = episode['attributes']
			item_tre = self.create_entries('STREAM', episode, 'episode',\
				{'TvShowTitle': show_title, 'Season': shorts['seasonNumber'],'Episode': shorts['episodeNumber']})
			item_tre.setLabel(f"[COLOR chartreuse]S{shorts['seasonNumber']:02}E{shorts['episodeNumber']:02}:"\
				f"[/COLOR] {shorts['name']}")
			self.add_dir_item(f"/play/{episode['id']}", item_tre)
		self.end_dir()

	def list_series(self):
		for series in self.fetch_disco_paginated(f"/content/shows?filter[primaryChannel.id]={DISCO_ID}"):
			shorts = series['attributes']
			if shorts['episodeCount'] == 0:
				continue
			item = self.create_entries('OTHERS', {'Title': shorts['name'], 'Plot': shorts.get('description'),\
				'Mediatype': 'tvshow'}, '', self.get_thumb('standard.png'))
			self.add_dir_item(f"/series/{series['id']}", item, True)
		self.end_dir()

	def show_special(self, series_id):
		if not series_id:
			return self.list_special()
		videos = list(self.fetch_disco_paginated("/content/videos"\
			f"?include=images,genres,show&filter[show.id]={series_id}"))
		if not videos:
			return
		for video in videos:
			for method in self.set_sort_methods(): xbmcplugin.addSortMethod(self.handle, method)
			if not str(video['attributes'].get('videoDuration')).isdecimal():
				continue
			norms = 'movie' if video['attributes'].get('videoType') == 'STANDALONE' else 'video'
			item = self.create_entries('STREAM', video, norms)
			self.add_dir_item(f"/play/{video['id']}", item)
		self.end_dir()

	def list_special(self):
		for series in self.fetch_disco_paginated(f"/content/shows?filter[primaryChannel.id]={DISCO_ID}"):
			shorts = series['attributes']
			if (shorts['episodeCount'] != 0 or shorts['videoCount'] <= 1):
				continue
			item_uno = self.create_entries('OTHERS', {'Title': shorts['name'], 'Plot': shorts.get('description'),\
				'Mediatype': 'tvshow'}, '', self.get_thumb('standard.png'))
			self.add_dir_item(f"/special/{series['id']}", item_uno, True)
		for clip in self.fetch_disco_paginated("/content/videos"\
			f"?include=images,show&filter[videoType]=CLIP&filter[primaryChannel.id]={DISCO_ID}"):
			show = clip['relationships']['show']['data']
			if show['attributes']['videoCount'] > 1 or not str(clip['attributes'].get('videoDuration')).isdecimal():
				continue
			item_due = self.create_entries('STREAM', clip, 'video')
			self.add_dir_item(f"/play/{clip['id']}", item_due)
		self.end_dir()

	def create_entries(self, target, metadata, medias='video', extras=None):
		picture = self.get_thumb('standard.png')
		if target == 'STREAM':
			shorts, online, (starting, airing) = metadata['attributes'], None, ("" for _ in range(2))
			listitem = xbmcgui.ListItem(shorts['name'])
			description = shorts.get('description')
			duration = shorts['videoDuration'] // 1000
			if str(shorts.get('publishStart'))[:4].isdecimal():
				starting = self.format_timestamp(self.parse_timestamp(shorts['publishStart']))
				airing = self.format_timestamp(self.parse_timestamp(shorts['publishStart']), display=True)
			if self.show_online in [0, 1] and str(shorts.get('publishEnd'))[:4].isdecimal():
				ending = self.parse_timestamp(shorts['publishEnd'])
				if self.show_online == 0:
					online = self.format_duration_user(ending - time())
				elif self.show_online == 1:
					online = self.translate(32221).format(self.format_timestamp_user(ending))
			if description is None: plot = online
			elif online is None: plot = description
			else: plot = f"{online}[CR][CR]{description}"
			story = ' ' if plot is None else plot
			try: picture = metadata['relationships']['images']['data'][0]['attributes']['src']
			except: picture = self.get_thumb('standard.png')
			listitem.setArt({'icon': self.get_icon(), 'thumb': picture, 'poster': picture, 'fanart': self.get_fanart()})
			listitem.setProperty('isPlayable', 'true')
			metadata = {'Title': shorts['name'], 'Plot': story, 'Duration': duration, 'Date': starting,\
				'Aired': airing, 'Mediatype': medias}
			if extras not in ['', None]: metadata.update(extras)
		else:
			listitem = xbmcgui.ListItem(metadata['Title'])
			if target == 'DEFAULT': metadata.update({'Plot': metadata.get('Plot', ' ')})
			elif target == 'OTHERS': metadata.update({'Plot': metadata.get('description', ' ')})
			listitem.setArt({'icon': self.get_icon(), 'thumb': extras, 'fanart': self.get_fanart()})
		if self.addon.getSetting('use_fanart') == 'true' and\
			not picture.endswith(('icon.png', 'standard.png', 'livestream.png', 'settings.png')):
			listitem.setArt({'fanart': picture})
		if KODI_VERSION >= 20:
			vinfo = listitem.getVideoInfoTag()
			vinfo.setTitle(metadata['Title'])
			if metadata.get('TvShowTitle', ''):
				vinfo.setTvShowTitle(metadata['TvShowTitle'])
			vinfo.setPlot(metadata['Plot'])
			if str(metadata.get('Duration')).isdecimal():
				vinfo.setDuration(int(metadata['Duration']))
			if str(metadata.get('Season')).isdecimal():
				vinfo.setSeason(int(metadata['Season']))
			if str(metadata.get('Episode')).isdecimal():
				vinfo.setEpisode(int(metadata['Episode']))
			if metadata.get('Date', ''):
				listitem.setDateTime(metadata['Date'])
			if metadata.get('Aired', ''):
				vinfo.setFirstAired(metadata['Aired'])
			if metadata.get('Mediatype', ''):
				vinfo.setMediaType(metadata['Mediatype'])
		else:
			listitem.setInfo('Video', metadata)
		return listitem

	def parse_timestamp(self, timestamp):
		return timegm(strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ'))

	def format_timestamp(self, terms, display=False):
		if KODI_VERSION >= 20 and display is False:
			return strftime('%Y-%m-%dT%H:%M', localtime(terms)) # 2023-07-23T12:30:00 / NEWFORMAT
		return strftime('%d.%m.%Y', localtime(terms)) # 23.07.2023 / OLDFORMAT

	def format_duration_user(self, duration):
		if duration < 60:
			return self.translate(32222).format(int(duration))
		elif duration < 3600:
			return self.translate(32223).format(int(duration // 60))
		elif duration < 86400:
			return self.translate(32224).format(int(duration // 3600))
		return self.translate(32225).format(int(duration // 86400))

	def format_timestamp_user(self, timestamp):
		if abs(timestamp - time()) <= 43200:
			actual = xbmc.getRegion('time')
		else:
			actual = xbmc.getRegion('dateshort')
		return strftime(actual, localtime(timestamp))

	def play_video(self, video_id):
		payload = {"deviceInfo":{"adBlocker":False,"drmSupported":True},"wisteriaProperties":{},"videoId":str(video_id)}
		video_info = self.fetch_disco('/playback/v3/videoPlaybackInfo', payload)
		#{"deviceInfo":
			#{'adBlocker':False,
			#'drmSupported':True,
			#'hdrCapabilities': ['SDR'],
			#'hwDecodingCapabilities': [],
			#'soundCapabilities': ['STEREO'],
			#},
			#'wisteriaProperties': {},
			#'videoId': str(video_id),
		#})
		for stream in video_info['data']['attributes']['streaming']:
			manifest_api = stream['type']
			try:
				manifest_kodi = MANIFEST_TYPES[manifest_api]
			except KeyError:
				self.log("Unknown manifest type {!r}".format(manifest_api), xbmc.LOGWARNING)
				continue
			drm = stream['protection']
			if drm['drmEnabled']:
				streamhelper = inputstreamhelper.Helper(manifest_kodi, drm=DRM_KODI)
			else:
				streamhelper = inputstreamhelper.Helper(manifest_kodi)
			if not streamhelper.check_inputstream():
				return
			item = xbmcgui.ListItem(path=stream['url'])
			item.setProperty('inputstream', streamhelper.inputstream_addon)
			item.setProperty('inputstream.adaptive.manifest_type', manifest_kodi)
			if drm['drmEnabled']:
				item.setProperty('inputstream.adaptive.license_type', DRM_KODI)
				licensing = f"{drm['schemes'][DRM_API]['licenseUrl']}|PreAuthorization={drm['drmToken']}"\
					"&Content-Type=application/octet-stream|R{SSM}|"
				item.setProperty('inputstream.adaptive.license_key', licensing)
			self.set_resolved(item, automatic=True)
			return

		self.log("No known manifest type found", xbmc.LOGERROR)
		xbmcgui.Dialog().notification(self.translate(32241), self.translate(32242), xbmcgui.NOTIFICATION_ERROR)

	def play_live(self):
		html_page = self.fetch('https://embed-zattoo.com/tele-5/?banner=false')
		token = (re.search(r"appToken = '([a-z0-9]*)'".encode(), html_page).group(1).decode())
		result = self.fetch_json_post_raw('https://embed-zattoo.com/zapi/watch',\
			(f"session_token={token}&uuid={make_uuid()}&device_type=&partner_site=tele5"\
			'&cid=tele-5&stream_type=dash&https_watch_urls=True').encode(),\
			headers = {
				'Origin': 'https://embed-zattoo.com',
				'Referer': 'https://embed-zattoo.com/tele-5/?banner=false',
				'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
				'Accept': 'application/json'})
		streamhelper = inputstreamhelper.Helper('mpd')
		if not streamhelper.check_inputstream():
			return
		item = xbmcgui.ListItem(path=result['stream']['url'])
		item.setProperty('inputstream', streamhelper.inputstream_addon)
		item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
		self.set_resolved(item)

	def fetch_disco_paginated(self, path):
		path += '&' if '?' in path else '?'
		path += 'page[size]=100'
		first_page = self.fetch_disco(path)
		for item in first_page['data']: yield item
		for page in range(2, first_page['meta']['totalPages']+1):
			result = self.fetch_disco(f"{path}&page[number]={page}")
			for item in result['data']: yield item

	def fetch_disco(self, path, data=None, headers={}):
		token = self.get_disco_token()
		all_headers = DISCO_HEADERS.copy()
		all_headers['Authorization'] = f"Bearer {token}"
		all_headers.update(headers)
		response = self.fetch_json(DISCO_HOST+path, data, all_headers)
		if 'included' in response:
			included = {(res['type'], res['id']): res for res in response['included']}
			if included:
				for inc in included.values():
					self.update_included(inc, included)
				self.update_included(response['data'], included)
		return response

	def update_included(self, data, included):
		def find_value(v):
			try: return included[v['type'], v['id']]
			except KeyError: return v

		def update_item(item):
			try: relations = item['relationships']
			except KeyError: return
			for value in relations.values():
				data = value['data']
				if isinstance(data, list):
					for i, item in enumerate(data): data[i] = find_value(item)
				else:
					value['data'] = find_value(data)

		if isinstance(data, list):
			for item in data: update_item(item)
		else:
			update_item(data)

	def fetch_json(self, url, data=None, headers={}):
		if data is not None: data = json.dumps(data).encode('ascii')
		headers.update({'Content-Type': 'application/json'})
		return self.fetch_json_post_raw(url, data, headers)

	def fetch_json_post_raw(self, url, data=None, headers={}):
		return self.urlopen(url, data, headers, json.load)

	def fetch(self, url, data=None, headers={}):
		return self.urlopen(url, data, headers, lambda f: f.read())

	def urlopen(self, url, data, headers, func):
		all_headers = COMMON_HEADERS.copy()
		all_headers.update(headers)
		request = Request(url, data, headers=all_headers)
		req = urlopen(request)
		try:
			return func(req)
		finally:
			req.close()

	def get_disco_token(self):
		try: return self.disco_token
		except AttributeError: pass
		response = self.fetch_json(f"{DISCO_HOST}/token?realm={DISCO_REALM}", headers=DISCO_HEADERS)
		token = response['data']['attributes']['token']
		self.disco_token = token
		return token

	def log(self, msg, level):
		xbmc.log(f"[{self.name} v.{self.version}] {str(msg)}", level)

	def set_sort_methods(self):
		return [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL,\
			xbmcplugin.SORT_METHOD_DURATION, xbmcplugin.SORT_METHOD_DATE]

	def add_dir_item(self, path, listitem, folder=False):
		path = urlunsplit(('plugin', self.plugin, path, '', ''))
		listitem.setPath(path)
		xbmcplugin.addDirectoryItem(self.handle, path, listitem, isFolder=folder)

	def end_dir(self):
		xbmcplugin.endOfDirectory(self.handle)

	def set_resolved(self, listitem, automatic=False):
		listitem.setProperty('isPlayable', 'true')
		listitem.setContentLookup(False)
		xbmcplugin.setResolvedUrl(self.handle, True, listitem)
		if automatic is True and self.addon.getSetting('force_stopping') == 'true':
			from .player import discoMaster
			discoMaster().start_signal()

	def translate(self, num):
		return self.addon.getLocalizedString(num)

	def get_icon(self):
		return xbmcvfs.translatePath(self.addon.getAddonInfo('icon'))
	def get_thumb(self, image):
		addon_folder = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
		return os.path.join(addon_folder, 'resources', 'media', image)
	def get_fanart(self):
		return xbmcvfs.translatePath(self.addon.getAddonInfo('fanart'))
