import cPickle as pickle
import json
import operator
import pysftp

class routerList(object):
	def __init__(self, routerList):
		self.routerList = []

	def addRouter(self, routerEntry):
		self.routerList.append(routerEntry)

class router(object):
	def __init__(self, cdp_entries):
		self.cdp_entries = []
		self.hostname = ''
		self.ipAddress = ''
		self.capabilities = ''

	def addCdpEntry(self, cdp_entry):
		self.cdp_entries.append(cdp_entry)

	def addHostname(self, hostname):
		self.hostname = hostname

	def addIpAddress(self, ipAddress):
		self.ipAddress = ipAddress

	def addCapability(self, capability):
		self.capabilities = capability

	def removeCDPEntry(self, interfaceName):
		#Updates cdp_entries to include only those that DO NOT match interfaceName
		self.cdp_entries = [cdpEntry for cdpEntry in self.cdp_entries if cdpEntry.srcPort != interfaceName]

class cdpEntry(object):
	def __init__(self, hostname):
		self.hostname = ''
		self.srcPort = ''
		self.dstPort = ''
		self.ipAddress = ''

	def addHostname(self, hostname):
		self.hostname = hostname
	def addIpAddress(self, ipAddress):
		self.ipAddress = ipAddress
	def addSrcPort(self, srcPort):
		self.srcPort = srcPort
	def addDstPort(self, dstPort):
		self.dstPort = dstPort

class linkEntry(object):
	def __init__(self, hostname):
		self.srcRouter = ''
		self.dstRouter = ''
		self.srcPort = ''
		self.dstPort = ''
		self.ipAddress = ''

	def addSrcRouter(self, hostname):
		self.srcRouter = hostname
	def addDstRouter(self, hostname):
		self.dstRouter = hostname
	def addIpAddress(self, ipAddress):
		self.ipAddress = ipAddress
	def addSrcPort(self, srcPort):
		self.srcPort = srcPort
	def addDstPort(self, dstPort):
		self.dstPort = dstPort

class intChangeList(object):
	def __init__(self, changeList):
		self.changeList = []

	def addChange(self, changeEntry):
		self.changeList.append(changeEntry)

class routerChanges(object):
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

def loadJSON(topology):
	#Load the topology to file
	with open('topology.json') as data_file:    
		data = json.load(data_file)
	#Get the information about nodes
	nodeList = data['nodeList']
	#For each node create a new object
	for idx, val in enumerate(nodeList):
		currentRouter = val
		newDevice = router([])
		newDevice.addHostname(currentRouter['hostname'])
		newDevice.addIpAddress(currentRouter['ipAddress'])
		newDevice.addCapability(currentRouter['deviceType'])
		topology.addRouter(newDevice)
	#Get the information for links
	linksList = data['linksList']
	linkEntries = []
	#For every link create a link object
	for idx, val in enumerate(linksList):
		currentLink = val
		newLink = linkEntry([])
		newLink.addDstRouter(currentLink['dstRouter'])
		newLink.addDstPort(currentLink['dstPort'])
		newLink.addSrcPort(currentLink['srcPort'])
		newLink.addIpAddress(currentLink['dstIpAddress'])
		newLink.addSrcRouter(currentLink['srcRouter'])
		linkEntries.append(newLink)
	#Call a function that ties links to nodes
	createCDP(linkEntries, topology)

def createCDP(linkEntries, topology):
	#iterate over the links
	for idx, val in enumerate(linkEntries):
		#Iterate over all routers
		for routerIDX, routerVal in enumerate(topology.routerList):
			#if the link source is the current router
			if routerVal.hostname == val.srcRouter:
				#Create a CDP entry and add it to the router
				cdpLine = cdpEntry([])
				cdpLine.addHostname(val.dstRouter)
				cdpLine.addSrcPort(val.srcPort)
				cdpLine.addDstPort(val.dstPort)
				cdpLine.addIpAddress(val.ipAddress)
				routerVal.addCdpEntry(cdpLine)

def formatInterfaces(topology):
	intChanges = intChangeList([])
	for idx, val in enumerate(topology.routerList):
		gigabitInts = []
		fastEthernetInts = []
		serialInts = []
		interfaceValues = []
		newValues = []
		for cdpIDX, cdpVal in enumerate(val.cdp_entries):
			if 'Gigabit' in cdpVal.srcPort:
				gigabitInts.append(cdpVal.srcPort)
			elif 'FastEthernet' in cdpVal.srcPort:
				fastEthernetInts.append(cdpVal.srcPort)
			elif 'Serial' in cdpVal.srcPort:
				serialInts.append(cdpVal.srcPort)
			#interfaceValues.append(cdpVal.srcPort)
		gigabitInts.sort()
		fastEthernetInts.sort()
		serialInts.sort()
		if len(gigabitInts)>0:
			interfaceValues = interfaceValues + gigabitInts
		if len(fastEthernetInts)>0:
			interfaceValues = interfaceValues + fastEthernetInts
		if len(serialInts)>0:
			interfaceValues = interfaceValues + serialInts
		localChanges = {}
		for intIDX, intVAL in enumerate(interfaceValues):
			if interfaceValues[intIDX] in localChanges:
				pass
			else:
				routerIntChanges = routerChanges([])
				routerIntChanges.addHostname(val.hostname)
				routerIntChanges.addOrignalPort(intVAL)
				newInterface = "GigabitEthernet0/" + str(len(localChanges) + 1)
				routerIntChanges.addNewPort(newInterface)
				intChanges.addChange(routerIntChanges)
				#print intChanges.changeList[0].hostname
				print routerIntChanges.hostname + " was: " + routerIntChanges.orignalPort + " now: " + routerIntChanges.newPort
				localChanges[intVAL] = newInterface
		intChanges.changeList.sort(key=operator.attrgetter('orignalPort'))
		#print intChanges
		pickle.dump(intChanges, open("interfaceChanges.p", "wb"))
		replaceInterfaces(topology, intChanges)

def replaceInterfaces(topology, intChanges):
	for i, changeEntry in enumerate(intChanges.changeList):
		for j, routerVal in enumerate(topology.routerList):
			for k, val in enumerate(routerVal.cdp_entries):
				if routerVal.hostname == intChanges.changeList[i].hostname and val.srcPort == intChanges.changeList[i].orignalPort:
					topology.routerList[j].cdp_entries[k].srcPort = intChanges.changeList[i].newPort
				elif val.hostname == intChanges.changeList[i].hostname and val.dstPort == intChanges.changeList[i].orignalPort:
					topology.routerList[j].cdp_entries[k].dstPort = intChanges.changeList[i].newPort

def main():
	topology = routerList([])
	loadJSON(topology)
	formatInterfaces(topology)
	pickle.dump(topology, open("simulationTopology.p", "wb"))
	routerDict = {}
	for j, routerVal in enumerate(topology.routerList):
		if routerVal.capabilities == 'Router':
			routerDict[routerVal.hostname] = routerVal.ipAddress
	print routerDict
	pickle.dump(routerDict, open("routerDictionary.p", "wb"))
	with pysftp.Connection('178.62.24.178', username='sftp', private_key='/home/rob/.ssh/id_rsa') as sftp:
		with sftp.cd('json-files'):
			sftp.put('topology.json')

if __name__ == "__main__":
	main()