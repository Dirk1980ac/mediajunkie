# -*- coding: utf-8 -*-

from resources.lib.common import *
from resources.lib.provider import Client


class realvitoMonitor(xbmc.Monitor):
	def __init__(self, *args, **kwargs):
		super(realvitoMonitor, self).__init__()
		self._changing = False

	def onSettingsChanged(self):
		self._changing = True
		self._enabling = (xbmc.LOGINFO if addon.getSetting('enable_debug') == 'true' else xbmc.LOGDEBUG)
		debug_MS("(service.onSettingsChanged[00]) ***** THE PROGRAM-SETTINGS OF THE SERVICE HAVE BEEN CHANGED *****", self._enabling)

class CronService():
	def __init__(self, *args, **kwargs):
		self._monitor = realvitoMonitor()
		self._traversing = Client(Client.SUPPORTED_ADDONS)
		self._warnings, self._trashings, self._debuggin = self.events_setter()
		self._stopping = False
		self._errornote = 0
		self._maximum = 3

	def current_os(self):
		COS = 'Unknown'
		PLATFORMS = ['System.Platform.Android', 'System.Platform.UWP', 'System.Platform.Windows', 'System.Platform.IOS', 'System.Platform.Darwin', 'System.Platform.OSX', 'System.Platform.TVOS', 'System.Platform.Linux', 'System.Platform.Linux.RaspberryPi']
		for each in PLATFORMS:
			if xbmc.getCondVisibility(each):
				COS = each.split('.')[-1]
				break
		return COS

	def events_setter(self):
		self._warnings = (True if addon.getSetting('show_warnings') == 'true' else False)
		self._trashings = (True if addon.getSetting('force_removing') == 'true' else False)
		self._debuggin = (xbmc.LOGINFO if addon.getSetting('enable_debug') == 'true' else xbmc.LOGDEBUG)
		self._monitor._changing = False
		return (self._warnings, self._trashings, self._debuggin)

	def start_signal(self):
		time.sleep(20)
		announce("####################################################################################################")
		announce(f"########## RUNNING: {addon_id} VERSION {addon_version} / ON PLATFORM: {self.current_os()} ##########")
		announce("############# Start the Service in nearly 3 minutes - wait for other Instances to close ############")
		announce("####################################################################################################")
		time.sleep(160)
		self.start_timer()

	def start_timer(self):
		while not self._monitor.abortRequested() and not self._stopping:
			self._warnings, self._trashings, self._debuggin = self.events_setter()
			if os.path.isdir(tempSTORE) and xbmcvfs.exists(Database):
				NEXTRUN = addon.getSetting('next_process')
				STORE_START = datetime(*(time.strptime(NEXTRUN[:19], '%Y-%m-%d %H:%M:%S')[0:6])) # 2024-03-09 14:10:00
				if datetime.now() > STORE_START:
					NEXT_START = datetime.now() + timedelta(seconds=3600) # Current time plus one Hour = Time for the next run of Crontab
					addon.setSetting('next_process', str(NEXT_START)[:19])
					debug_MS(f"(service.start_timer[1]) >> SERVICE INIT >> STORED DATE : {str(STORE_START)} >> (NEXT START : {str(NEXT_START)[:19]})", self._debuggin)
					self.load_rebuild()
					self._waiting = 3605
				else:
					NEXT_WAITS = (round((STORE_START - datetime.now()) / timedelta(seconds=1)) + 5)
					MESSAGE = f"{NEXT_WAITS % 3600 // 60} MINS {NEXT_WAITS % 60} SECS" if (NEXT_WAITS % 3600 // 60) > 0 else f"{NEXT_WAITS % 60} SECS"
					debug_MS(f"(service.start_timer[1]) >> SERVICE INIT >> NEXT SCHEDULED EXECUTION IN: + {MESSAGE} + , INTERVAL IS SET TO ** 1 HOUR **", self._debuggin)
					self._waiting = NEXT_WAITS # Stored time minus Current time = Time to wait in Seconds for next run of Crontab
			else:
				log(f">>>>>>>>>>>>>>>>>> PAUSING: {addon_id} VERSION {addon_version} / ON PLATFORM: {self.current_os()} <<<<<<<<<<<<<<<<<<")
				log(">>>>>>>>>>>>>>!!! There is currently no *Crontab-Database* on your System, so the Service is paused !!!<<<<<<<<<<<<<")
				self._waiting = 3605
			if self._monitor.waitForAbort(int(self._waiting)):
				break
		else:
			time.sleep(20)
			failing("▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼")
			failing(f">>>>>>>>>>>>>>>>>> STOPPING: {addon_id} VERSION {addon_version} / ON PLATFORM: {self.current_os()} <<<<<<<<<<<<<<<<<<")
			failing(">>>>>>>>>>>!!! The Service was forcibly terminated by the System or due to the max. Error rate reached !!!<<<<<<<<<<<")
			failing("▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")

	def load_rebuild(self):
		if not self._stopping and not xbmc.getCondVisibility('Library.IsScanningVideo'):
			debug_MS("(service.load_rebuild[1]) ########## STARTING LOOP ... ##########", self._debuggin)
			position, lock_time, (COMBI_TASKS, COMBI_WORKS) = 0, 3, ([] for _ in range(2))
			addon.setSetting('program_locked', 'false')
			try:
				conn = sqlite3.connect(Database)
				cur = conn.cursor()
				cur.execute('SELECT * FROM stocks')
				for (stunden, url, name, last, source) in cur.fetchall():
					SUFFIX = url.split('@@', 1)[1].split('&', 1)[0] if '@@' in url else ""
					name += f"  ({SUFFIX})" if len(SUFFIX) == 4 else f"  ({SUFFIX.replace('es', 'e')})" if SUFFIX.startswith(('Staffel', 'Series', 'Movies')) else '  (Serie)'
					debug_MS(f"(service.load_rebuild[2]) ######## CONTROL-SESSION FOR >> TITLE : {name} || LASTUPDATE : {last} ########", self._debuggin)
					STORE_TIME = datetime(*(time.strptime(last[:19], '%Y-%m-%d %H:%M:%S')[0:6])) # 2024-03-09 14:10:00
					FEEDBACK, ROUTED, ALLOWED = self.access_permission(url)
					if datetime.now() > STORE_TIME + timedelta(hours=stunden):
						if ALLOWED is True:
							position += 1
							log(f"(service.load_rebuild[2]) ######## STARTING-ACTION FOR >> TITLE : {name} || LASTUPDATE : {last} || ADDON : {FEEDBACK} ########")
							COMBI_TASKS.append([position, url, ROUTED])
						else:
							log(f"(service.load_rebuild[2]) ######## DO NOTHING FOR >> TITLE : {name} || LASTUPDATE : {last} ########")
							log(f"(service.load_rebuild[2]) #### ERROR #### REASON : {FEEDBACK} ########")
				if COMBI_TASKS:
					COMBI_WORKS = self.multi_workflows(COMBI_TASKS)
					if COMBI_WORKS:
						NEXT_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						for counter, builtin, success in sorted(COMBI_WORKS, key=lambda cn: int(cn[0])):
							if success is True:
								debug_MS(f"(service.load_rebuild[3]) ######## SUCCESSFULLY COMPLETED >> UPDATE-TIME : {str(NEXT_TIME)} || EXTERN-URL : {builtin} ########", self._debuggin)
								cur.execute('UPDATE stocks SET last = ? WHERE url = ?', (NEXT_TIME, builtin))
								conn.commit()
								lock_time += 3 # 3 seconds plus 3 seconds for every execution - Time period after which the Process ends and the program is unlocked
			except:
				addon.setSetting('program_locked', 'false')
				conn.rollback() # Roll back any Change if something goes wrong
				if self._warnings is True:
					dialog.notification(translation(30521).format('Daten aktualisieren'), translation(30522), icon, 10000)
				formatted_lines = traceback.format_exc().splitlines()
				self._errornote += 1
				if self._errornote >= self._maximum:
					failing(f"(service.load_rebuild[2]) ▼▼▼ ERROR - ENDING - ERROR ▼▼▼\n{formatted_lines[1]} \n{formatted_lines[2]} \n{formatted_lines[3]} ...\n▲▲▲▲▲ (now: {self._errornote}/max: {self._maximum}) ...Ending Service ▲▲▲▲▲")
					self._stopping = True
				else:
					failing(f"(service.load_rebuild[2]) ▼▼▼ ERROR - CONTINUE - ERROR ▼▼▼\n{formatted_lines[1]} \n{formatted_lines[2]} \n{formatted_lines[3]} ...\n▲▲▲▲▲ (now: {self._errornote}/max: {self._maximum}) ...Continue Service ▲▲▲▲▲")
			finally:
				cur.close()
				conn.close()
			debug_MS(f"(service.load_rebuild[4]) >> THE PROGRAM-OVERVIEW IS BLOCKED FOR >> {str(lock_time)} SECONDS <<", self._debuggin)
			time.sleep(lock_time)
			addon.setSetting('program_locked', 'false')
			debug_MS("(service.load_rebuild[5]) ########## ... ENDING LOOP ##########", self._debuggin)

	def access_permission(self, EXTERN_URL, default=False):
		DATAS, RECORDS = [], self._traversing.get_records()
		DATAS = [obj for obj in RECORDS['specifications'] if obj.get('route') in EXTERN_URL]
		debug_MS(f"(service.access_permission[1]) XXXXX EXTERN-URL : {EXTERN_URL} XXXXX", self._debuggin)
		if DATAS:
			if xbmc.getCondVisibility(f"System.HasAddon({DATAS[0]['route']})"):
				self._varSetting = xbmcaddon.Addon(f"{DATAS[0]['route']}").getSetting(f"{DATAS[0]['branch']}")
				if self._varSetting in ['false', 'true']:
					self._switch = (True if self._varSetting == 'true' else False)
					if self._switch is True:
						return (DATAS[0]['name'], DATAS[0]['route'], self._switch)
					else:
						return (f"XXX THE LIBRARY-FUNCTION OF THE ADDON *{DATAS[0]['name']}* IS NOT ACTIVATED XXX", DATAS[0]['route'], self._switch)
				return (f"XXX THE SETTING YOU ARE LOOKING FOR FROM *{DATAS[0]['route']}* WAS NOT FOUND XXX", DATAS[0]['route'], default)
			return (f"XXX THE REQUIRED ADDON *{DATAS[0]['name']}* IS NOT INSTALLED/ACTIVATED XXX", DATAS[0]['route'], default)
		return ('XXX NO ENTRY FOUND IN THE LIST FOR THE ADDON YOU ARE LOOKING FOR XXX', 'UNKNOWN', default)

	def multi_workflows(self, MURLS):
		addon.setSetting('program_locked', 'true')
		COMBI_NEW = []
		NUMBER = len(MURLS)
		def update_specs(POS, TOPICS, PLUGIN):
			try:
				debug_MS(f"(service.multi_workflows[1]) >> SEND EXECUTION TO EXTERN >> POSITION : {str(POS)} >> COMMAND : {TOPICS} XXXXX", self._debuggin)
				URL_UNO, NAME_UNO = TOPICS.split('&url=')[1].split('&name=')[0], TOPICS.split('&name=')[1]
				URL_DUE, NAME_DUE = quote_plus(URL_UNO), quote_plus(NAME_UNO)
				xbmc.executebuiltin(f"RunPlugin(plugin://{PLUGIN}/?mode=generatefiles&url={URL_DUE}&name={NAME_DUE})")
				return [POS, TOPICS, True]
			except:
				failing(f"(service.multi_workflows[1]) ERROR - BUILTIN - ERROR ##### POSITION : {str(POS)} === COMMAND : {TOPICS} #####")
				return [POS, TOPICS, False]
		with ThreadPoolExecutor(NUMBER) as executor:
			picker = [executor.submit(update_specs, pos, navi, route) for pos, navi, route in MURLS]
			wait(picker, timeout=20, return_when=ALL_COMPLETED)
			for ii, future in enumerate(as_completed(picker), 1):
				try:
					COMBI_NEW.append(future.result())
				except Exception as e:
					failing(f"(service.multi_workflows[2]) ERROR - EXEPTION - ERROR ##### FUTURE_CONNECT : {future.result()} === FAILURE : {str(e)} #####")
					executor.shutdown()
			return COMBI_NEW

if __name__ == '__main__':
	procedure = CronService()
	procedure.start_signal()
	del procedure
