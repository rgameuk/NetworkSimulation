import pickle
from ciscoconfparse import CiscoConfParse

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
	interfaceChanges = intChangeList([])
	interfaceChanges = pickle.load(open("interfaceChanges.p", "rb"))
	
	with open('./config-files/r2', 'r') as f:
		config = f.read()
		f.close()
	config = config.partition('config-register 0x2102')[2]
	with open('./config-files/r2.short', 'w') as f:
		f.write(config)
	#print config

	p = CiscoConfParse('./config-files/r2.short')

	for i, changeEntry in enumerate(interfaceChanges.changeList):
		if changeEntry.hostname == 'R2':
			p.replace_lines(changeEntry.orignalPort, changeEntry.newPort)

	for obj in p.find_objects(r'^interface Serial'):
		obj.delete(recurse=True)

	for obj in p.find_objects(r'^interface FastEthernet'):
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

	p.save_as('./config-files/r2.edited')