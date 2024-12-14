# -*- coding: utf-8 -*-

'''
    Copyright (C) 2024 realvito

    Crontab für andere Addons

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib.common import *
from resources.lib import navigator
name, url, mode, shortENTRY, stunden, source = build_constants()


def run():
	if mode == 'root': ##### Delete old Files in Userdata-Folder 'settings' to cleanup old Entries #####
		DONE = False    ##### [service.cron.autobiblio v.2.1.3] - 26.05.2024 #####
		firstSCRIPT = xbmcvfs.translatePath(os.path.join(f"special://home{os.sep}addons{os.sep}{addon_id}{os.sep}lib{os.sep}")).encode('utf-8').decode('utf-8')
		UNO = xbmcvfs.translatePath(os.path.join(firstSCRIPT, 'only_at_FIRSTSTART'))
		if xbmcvfs.exists(UNO):
			AUTOBIB = xbmcvfs.translatePath(os.path.join(f"special://home{os.sep}userdata{os.sep}addon_data{os.sep}{addon_id}{os.sep}")).encode('utf-8').decode('utf-8')
			OLD_SETTINGS = xbmcvfs.translatePath(os.path.join(AUTOBIB, 'settings.xml'))
			try:
				xbmc.executeJSONRPC(f'{{"jsonrpc":"2.0", "id":1, "method":"Addons.SetAddonEnabled", "params":{{"addonid":"{addon_id}", "enabled":false}}}}')
				if xbmcvfs.exists(OLD_SETTINGS):
					xbmcvfs.delete(OLD_SETTINGS) # Delete OLD_SETTINGS File
			except: pass
			xbmcvfs.delete(UNO)
			xbmc.executeJSONRPC(f'{{"jsonrpc":"2.0", "id":1, "method":"Addons.SetAddonEnabled", "params":{{"addonid":"{addon_id}", "enabled":true}}}}')
			xbmc.sleep(500)
			DONE = True
		else:
			DONE = True
		if DONE is True: navigator.mainMenu()
	elif mode == 'adddata':
		navigator.create_table()
		debug_MS("(navigator.adddata[1]) ########## STARTING INSERT ... ##########")
		debug_MS(f"(navigator.adddata[2]) ### Name = {name} || Stunden = {str(stunden)} || URL-1 = {url} || Source = {source} ###")
		navigator.insert_table(name, stunden, url, source)
		debug_MS("(navigator.adddata[3]) ########## ... ENDING INSERT ##########")
		navigator.make_listing(url)
	elif mode == 'delete_table':
		navigator.delete_table(shortENTRY, url, source)
	elif mode == 'delete_storage':
		navigator.delete_storage()

run()
