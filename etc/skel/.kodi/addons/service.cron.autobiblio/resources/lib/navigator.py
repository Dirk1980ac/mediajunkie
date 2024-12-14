# -*- coding: utf-8 -*-

from .common import *


if not xbmcvfs.exists(tempSTORE):
	xbmcvfs.mkdirs(tempSTORE)

def mainMenu():
	if addon.getSetting('program_locked') == 'false':
		if not xbmcvfs.exists(os.path.join(dataPath, 'settings.xml')):
			xbmcvfs.mkdirs(dataPath)
			xbmc.executebuiltin(f"Addon.OpenSettings({addon_id})")
		if xbmcvfs.exists(os.path.join(dataPath, 'settings.xml')):
			if os.path.isdir(tempSTORE) and xbmcvfs.exists(Database):
				xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
				debug_MS(f"(navigator.mainMenu) ===== STARTING 'mainMenu' ===== DELETING ENTRIES FROM CRONTAB AND SYSTEM ??? = {str(forceTrash)} =====")
				try:
					conn = sqlite3.connect(Database)
					cur = conn.cursor()
					cur.execute('SELECT * FROM stocks')
					for (stunden, url, name, last, source) in cur.fetchall():
						shortENTRY = name
						SUFFIX = url.split('@@', 1)[1].split('&', 1)[0] if '@@' in url else ""
						name += translation(30601).format(SUFFIX) if len(SUFFIX) == 4 else translation(30602).format(SUFFIX.replace('es', 'e')) if SUFFIX.startswith(('Staffel', 'Series', 'Movies')) else translation(30603)
						shortENTRY += f"  ({SUFFIX.replace('es', 'e')})" if '@@' in url else '  (Serie)'
						source = xbmcvfs.translatePath(os.path.join(source, '')) if source.startswith('special://') else source
						newSOURCE = source[::-1].replace('Jahr '[::-1], ''[::-1], 1)[::-1] if len(SUFFIX) == 4 and source.endswith('Jahr '+SUFFIX) else source
						debug_MS(f"(navigator.mainMenu[1]) +++++ shortENTRY = {shortENTRY} || STUNDEN = {str(stunden)} || lastUPDATE = {last} || newSOURCE = {newSOURCE} || URL = {url} +++++")
						if newSOURCE != 'standard' and os.path.isdir(newSOURCE) and forceTrash is True:
							addDir(translation(30604).format(name), icon, {'mode': 'delete_table', 'url': url, 'shortENTRY': shortENTRY, 'source': source})
						elif newSOURCE == 'standard' or forceTrash is False:
							addDir(translation(30605).format(name), icon, {'mode': 'delete_table', 'url': url, 'shortENTRY': shortENTRY, 'source': source})
				except:
					if enableWARNINGS is True:
						dialog.notification(translation(30521).format('Menü anzeigen'), translation(30522), icon, 10000)
					failing(f"(navigator.mainMenu[1]) ▼▼▼ ERROR - SQL - ERROR ▼▼▼\n{traceback.format_exc()} ▲▲▲▲▲")
				finally:
					cur.close()
					conn.close()
			else:
				CONFIRM = dialog.ok(addon_id, translation(30501))
				if CONFIRM:
					xbmc.sleep(500)
					xbmc.executebuiltin('Action(PreviousMenu)')
	else:
		CONFIRM = dialog.ok(addon_id, translation(30502))
		if CONFIRM:
			xbmc.sleep(500)
			xbmc.executebuiltin('Action(PreviousMenu)')
	xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=True, cacheToDisc=False)

def create_table():
	conn = sqlite3.connect(Database)
	cur = conn.cursor()
	try:
		cur.execute('CREATE TABLE IF NOT EXISTS stocks (stunden INTEGER, url TEXT PRIMARY KEY, name TEXT, last DATETIME)')
		try:
			cur.execute('ALTER TABLE stocks ADD COLUMN source TEXT')
		except sqlite3.OperationalError: pass
		conn.commit()
	except :
		if enableWARNINGS is True:
			dialog.notification(translation(30521).format('Tabelle erstellen'), translation(30522), icon, 10000)
		failing(f"(navigator.create_table[1]) ▼▼▼ ERROR - CREATE - ERROR ▼▼▼\n{traceback.format_exc()} ▲▲▲▲▲")
	finally:
		cur.close()
		conn.close()

def insert_table(name, stunden, url, source):
	last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	try:
		conn = sqlite3.connect(Database)
		conn.text_factory = str
		cur = conn.cursor()
		cur.execute('INSERT OR REPLACE INTO stocks VALUES (?,?,?,?,?)', (int(stunden), url, name, last, source))
		conn.commit()
	except:
		conn.rollback() # Roll back any Change if something goes wrong
		if enableWARNINGS is True:
			dialog.notification(translation(30521).format('Eintrag einfügen'), translation(30522), icon, 10000)
		failing(f"(navigator.insert_table[1]) ▼▼▼ ERROR - INSERT - ERROR ▼▼▼\n{traceback.format_exc()} ▲▲▲▲▲")
	finally:
		cur.close()
		conn.close()

def delete_table(shortENTRY, url, source):
	SUFFIX = url.split('@@', 1)[1].split('&', 1)[0] if '@@' in url else False
	source = xbmcvfs.translatePath(os.path.join(source, '')) if source.startswith('special://') else source
	newSOURCE = source[::-1].replace('Jahr '[::-1], ''[::-1], 1)[::-1] if SUFFIX and len(SUFFIX) == 4 and source.endswith('Jahr '+SUFFIX) else source
	FIRST_BASE = os.sep.join(source.split(os.sep)[:-1]) if SUFFIX and source != 'standard' else False
	CONFIRM = dialog.yesno(addon_id, translation(30503), nolabel=translation(30504), yeslabel=translation(30505))
	if CONFIRM < 1: return False # The User has clicked on "Cancel" or "Nothing", so we simply have to exit the GUI here.
	else:
		try:
			conn = sqlite3.connect(Database, isolation_level=None)
			conn.text_factory = str
			cur = conn.cursor()
			cur.execute('DELETE FROM stocks WHERE url = ?', (url,))
			cur.execute('VACUUM')
			conn.commit()
			if newSOURCE != 'standard' and os.path.isdir(newSOURCE) and forceTrash is True:
				shutil.rmtree(newSOURCE, ignore_errors=True)
				log(f"(navigator.delete_table[1]) ~~~~~~~~ DELETING FROM CRONTAB AND SYSTEM >> FOLDER = {str(source)} || TITLE = {shortENTRY} ~~~~~~~~")
				if FIRST_BASE and len([f for f in os.listdir(FIRST_BASE)]) == 1:
					shutil.rmtree(FIRST_BASE, ignore_errors=True)
					log(f"(navigator.delete_table[2]) ~~~~~~~~ LAST TURN >> DELETING FROM SYSTEM >> BASE-FOLDER = {str(FIRST_BASE)} ~~~~~~~~")
				xbmc.sleep(500)
				xbmc.executebuiltin('Container.Refresh')
				dialog.notification(translation(30523), translation(30524).format(shortENTRY), icon, 10000)
			elif newSOURCE == 'standard' or forceTrash is False:
				dialog.ok(addon_id, translation(30506))
				log(f"(navigator.delete_table[1]) ~~~~~~~~ DELETING ONLY FROM CRONTAB >> TITLE = {shortENTRY} ~~~~~~~~")
				xbmc.sleep(500)
				xbmc.executebuiltin('Container.Refresh')
		except:
			conn.rollback() # Roll back any Change if something goes wrong
			if enableWARNINGS is True:
				dialog.notification(translation(30521).format('Eintrag löschen'), translation(30522), icon, 10000)
			failing(f"(navigator.delete_table[3]) ▼▼▼ ERROR - DELETE - ERROR ▼▼▼\n({shortENTRY}) received... ({traceback.format_exc()}) ...delete Name in List failed ▲▲▲▲▲")
		finally:
			cur.close()
			conn.close()

def make_listing(url):
	debug_MS(f"(navigator.make_listing[1]) XXXXX SEND COMMAND TO EXTERN-ADDON = {url} XXXXX")
	URL_ONE, NAME_ONE = url.split('&url=')[1].split('&name=')[0], url.split('&name=')[1]
	URL_TWO, NAME_TWO, PLUGIN_TWO = quote_plus(URL_ONE), quote_plus(NAME_ONE), url.split('/?mode=')[0]
	xbmc.executebuiltin(f"RunPlugin({PLUGIN_TWO}/?mode=generatefiles&url={URL_TWO}&name={NAME_TWO})")

def delete_storage():
	if os.path.isdir(tempSTORE) and xbmcvfs.exists(Database):
		CONFIRM = dialog.yesno(addon_id, translation(30507), nolabel=translation(30504), yeslabel=translation(30505))
		if CONFIRM < 1: return # The User has clicked on "Cancel" or "Nothing", so we simply have to exit the GUI here.
		else:
			shutil.rmtree(tempSTORE, ignore_errors=True)
			xbmc.sleep(1000)
			dialog.notification(translation(30523), translation(30525), icon, 10000)
			log(f"(navigator.delete_storage[1]) ~~~~~~~~ DELETING COMPLETE DATABASE OF CRONTAB ... *{Database}* ... SUCCESS ~~~~~~~~")
	else: dialog.ok(addon_id, translation(30508))

def addDir(name, image, params={}, folder=True):
	uws = build_mass(params)
	LDM = xbmcgui.ListItem(name, offscreen=True)
	description = f"[B]{translation(30606)}{name.split(': ', 1)[0]}[/B][CR][CR]{name.split(': ', 1)[1]}"
	if KODI_ov20:
		vinfo = LDM.getVideoInfoTag()
		vinfo.setTitle(name), vinfo.setPlot(description)
	else:
		LDM.setInfo('Video', {'Title': name, 'Plot': description})
	LDM.setArt({'icon': icon, 'thumb': image, 'poster': image})
	xbmcplugin.setContent(int(sys.argv[1]), 'files')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=uws, listitem=LDM, isFolder=folder)
