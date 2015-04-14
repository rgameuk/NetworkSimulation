import pickle
from ciscoconfparse import CiscoConfParse
import shutil
import argparse

class intChangeList(object):
	#List object to hold router interface changes
	def __init__(self, changeList):
		self.changeList = []

	def addChange(self, changeEntry):
		self.changeList.append(changeEntry)

class routerChanges(object):
	#Object to hold the interface changes made to a device
	def __init__(self, hostname):
		self.hostname = ''
		self.orignalPort = ''
		self.newPort = ''

	def addHostname(self, hostname):
		self.hostname = hostname
	def addOrignalPort(self, orignalPort):
		self.orignalPort = orignalPort
	def addNewPort(self, newPort):
		self.newPort = newPort

if __name__ == "__main__":
	configLocation = '/home/rob/NetworkSimulation/python-scripts/config-files'
	interfaceChanges = intChangeList([])
	interfaceChanges = pickle.load(open("interfaceChanges.p", "rb"))
	routerList = pickle.load(open("routerDictionary.p", "rb"))
	copyFiles = True

	parser = argparse.ArgumentParser()
	parser.add_argument("--noCopy", help="Do not copy configuration files from rancid",
                    action="store_true")
	args = parser.parse_args()
	if args.noCopy:
		copyFiles = False

	if copyFiles == True:
		for key, value in routerList.iteritems():
			shutil.copy('/var/lib/rancid/Discovered/configs/' + key.lower(), configLocation)
	
	try:
		for key, value in routerList.iteritems(): 
			with open('./config-files/' + key.lower(), 'r') as f:
				config = f.read()
				f.close()
			oldConfig = config.partition('version')
			configList = [oldConfig[i] for i in (1, 2)]
			config = configList[0] + configList[1]
			with open('./config-files/' + key.lower() + '.short', 'w') as f:
				f.write(config)

			p = CiscoConfParse('./config-files/' + key.lower() + '.short')

			for i, changeEntry in enumerate(interfaceChanges.changeList):
				oldPort = changeEntry.orignalPort
				if changeEntry.hostname == key:
					if 'Serial' in changeEntry.orignalPort:
						obj = p.find_objects(changeEntry.orignalPort)
						print obj
						if (obj[0].has_child_with(r' bandwidth') == False):
							obj[0].append_to_family(' bandwidth 2000')
					if 'FastEthernet' in changeEntry.orignalPort:
						obj = p.find_objects(changeEntry.orignalPort)
						print obj
						if (obj[0].has_child_with(r' bandwidth') == False):
							obj[0].append_to_family(' bandwidth 100000')
					p.replace_lines(changeEntry.orignalPort, changeEntry.newPort)


			for obj in p.find_objects(r'Serial'):
				obj.delete(recurse=True)

			for obj in p.find_objects(r'FastEthernet'):
				obj.delete(recurse=True)

			for obj in p.find_objects(r'^interface'):
				obj.delete_children_matching(r'clock rate')

			p.insert_before('interface GigabitEthernet0/1', 'interface GigabitEthernet0/0', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', '!', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', ' no shutdown', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', ' speed auto', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', ' duplex auto', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', ' no ip address', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', '! Configured on launch', exactmatch=True, atomic=False)
			p.insert_after('interface GigabitEthernet0/0', ' description OOB Management', exactmatch=True, atomic=False)

			for obj in p.find_objects(r'^line vty'):
				obj.delete(recurse=True)
			for obj in p.find_objects(r'^enable password'):
				obj.delete()
			for obj in p.find_objects(r'^login password'):
				obj.delete()

			p.insert_before('end', 'line vty 0 4', exactmatch=True, atomic=False)
			p.insert_after('line vty 0 4', ' no login', exactmatch=True, atomic=False)
			p.insert_after(' no login', ' privilege level 15', exactmatch=True, atomic=False)
			p.insert_after('line vty 0 4', ' transport input telnet ssh', exactmatch=True, atomic=False)

			p.save_as('./config-files/' + key.lower() + '.edited')
	except:
		print key + ' is not a valid Cisco configuration file. Aborting configuration edits'