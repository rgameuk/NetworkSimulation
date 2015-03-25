import pickle
from ciscoconfparse import CiscoConfParse
import shutil
import operator

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
	scriptLocation = '/home/rob/NetworkSimulation/python-scripts/config-files'
	interfaceChanges = intChangeList([])
	interfaceChanges = pickle.load(open("interfaceChanges.p", "rb"))
	routerList = pickle.load(open("routerDictionary.p", "rb"))

	for key, value in routerList.iteritems():
		shutil.copy('/var/lib/rancid/Discovered/configs/' + key.lower(), scriptLocation)
	
	for key, value in routerList.iteritems(): 
		with open('./config-files/' + key.lower(), 'r') as f:
			config = f.read()
			f.close()
		config = config.partition('config-register 0x2102')[2]
		with open('./config-files/' + key.lower() + '.short', 'w') as f:
			f.write(config)
		#print config

		p = CiscoConfParse('./config-files/' + key.lower() + '.short')

		for i, changeEntry in enumerate(interfaceChanges.changeList):
			oldPort = changeEntry.orignalPort
			if changeEntry.hostname == key:
				if 'Serial' in changeEntry.orignalPort:
					obj = p.find_objects(changeEntry.orignalPort)
					#print obj
					#if (obj[0].has_child_with(r' bandwidth') == False):
					#	obj[0].append_to_family(' bandwidth 2000')
				if 'FastEthernet' in changeEntry.orignalPort:
					obj = p.find_objects(changeEntry.orignalPort)
					#print obj
					#if (obj[0].has_child_with(r' bandwidth') == False):
					#	obj[0].append_to_family(' bandwidth 100000')
				p.replace_lines(changeEntry.orignalPort, changeEntry.newPort)


		for obj in p.find_objects(r'Serial'):
			obj.delete(recurse=True)

		for obj in p.find_objects(r'FastEthernet'):
			obj.delete(recurse=True)

		for obj in p.find_objects(r'^interface'):
			obj.delete_children_matching(r'clock rate')

		p.insert_before('interface GigabitEthernet0/1', 'interface GigabitEthernet0/0', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', '! New interfaces start below', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', '!', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', ' description OOB Management', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', ' no shutdown', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', ' speed auto', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', ' duplex auto', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', ' no ip address', exactmatch=True, atomic=False)
		p.insert_after('interface GigabitEthernet0/0', '! Configured on launch', exactmatch=True, atomic=False)

		all_intfs = p.find_objects(r"^interface GigabitEthernet0/[1-9]")
		all_intfs.sort(key=operator.attrgetter('text'))

		for obj in p.find_objects(r"^interface GigabitEthernet0/[1-9]"):
			obj.delete(recurse=True)

		# Look at config file on R3 for information - Serial and Fa interfaces out of order

		interfaceStart = '! New interfaces start below'

		print 'Changes to: ' + key

		for obj in all_intfs:
			print 'Adding: ' + obj.text + ' after ' + interfaceStart
			commentStart = '! start of ' + obj.text
			p.insert_after(interfaceStart, commentStart, exactmatch=True, atomic=True)
			commentEnd = '! end of ' + obj.text
			p.insert_after(commentStart, commentEnd, exactmatch=True, atomic=True)
			interfaceLine = obj.text
			children = obj.children
			p.insert_after(commentStart, interfaceLine, exactmatch=True, atomic=True)
			for child in children:
				print 'adding ' + child.text + ' before ' + commentEnd
				p.insert_before(commentEnd, child.text, exactmatch=True, atomic=True)
			interfaceStart = commentEnd

			
		#for intLine in all_intfs:
		#	p.insert_after(previousInterface, intLine.text, exactmatch=True, atomic=False)
		#	previousInterface = intLine.text


		p.save_as('./config-files/' + key.lower() + '.edited')