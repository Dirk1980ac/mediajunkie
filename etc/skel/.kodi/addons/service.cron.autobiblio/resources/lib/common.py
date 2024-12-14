# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import shutil
import time
import _strptime
from datetime import datetime, timedelta
import sqlite3
import traceback
from concurrent.futures import *
from urllib.parse import parse_qsl, urlencode, quote_plus, unquote_plus


dialog									= xbmcgui.Dialog()
addon									= xbmcaddon.Addon()
addon_id							= addon.getAddonInfo('id')
addon_name						= addon.getAddonInfo('name')
addon_version					= addon.getAddonInfo('version')
addon_desc						= addon.getAddonInfo('description')
addonPath							= xbmcvfs.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath								= xbmcvfs.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
tempSTORE						= xbmcvfs.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
Database							= xbmcvfs.translatePath(os.path.join(tempSTORE, 'MyTimeOrders.db'))
icon										= os.path.join(addonPath, 'resources', 'icon.png')
enableWARNINGS				= (True if addon.getSetting('show_warnings') == 'true' else False)
forceTrash							= (True if addon.getSetting('force_removing') == 'true' else False)
DEB_LEVEL							= (xbmc.LOGINFO if addon.getSetting('enable_debug') == 'true' else xbmc.LOGDEBUG)
PROGRAM_LOCK				= addon.getSetting('program_locked') == 'true'
NEXT_PROCESS					= addon.getSetting('next_process')
KODI_ov20						= int(xbmc.getInfoLabel('System.BuildVersion')[0:2]) >= 20
KODI_un21						= int(xbmc.getInfoLabel('System.BuildVersion')[0:2]) <= 20

def translation(id):
	return addon.getLocalizedString(id)

def announce(msg, worth=xbmc.LOGINFO):
	return xbmc.log(str(msg), worth)

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content, phase=DEB_LEVEL):
	log(content, phase)

def log(msg, level=xbmc.LOGINFO):
	return xbmc.log(f"[{addon_id} v.{addon_version}]{str(msg)}", level)

def build_mass(body):
	return f"{sys.argv[0]}?{urlencode(body)}"

def build_constants():
	params = dict(parse_qsl(sys.argv[2][1:]))
	name = unquote_plus(params.get('name', ''))
	url = unquote_plus(params.get('url', ''))
	mode = unquote_plus(params.get('mode', 'root'))
	shortENTRY = unquote_plus(params.get('shortENTRY', ''))
	stunden = unquote_plus(params.get('stunden', ''))
	source = unquote_plus(params.get('source', 'standard'))
	return (name, url, mode, shortENTRY, stunden, source)
