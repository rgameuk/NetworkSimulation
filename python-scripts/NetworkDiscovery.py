import os
import subprocess
import string
import re
import cPickle as pickle
import json
import pysftp
import operator
import collections
import copy

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

		#for cdpIDX, cdpVal in enumerate(self.cdp_entries):
		#	print self.cdp_entries[cdpIDX].hostname + ' on ' + self.cdp_entries[cdpIDX].srcPort
		#	if cdpVal.srcPort == interfaceName:
		#		#print 'Deleting: ' + self.cdp_entries[cdpIDX].hostname + ' on ' + self.cdp_entries[cdpIDX].srcPort
		#		self.cdp_entries[cdpIDX] = cdpEntry([])

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

class jsonObject(object):
	def __init__(self, linksList):
		self.linksList = []
		self.nodeList = []
	def appendLink(self, newLink):
		self.linksList.append(newLink)
	def appendNode(self, newNode):
		self.nodeList.append(newNode)

class switchUpdate(object):
	def __init__(self, hostname):
		self.switchHostname = ''
		self.dstHostname = ''
		self.switchport = ''

	def addswitchHostname(self, hostname):
		self.switchHostname = hostname
	def adddstHostname(self, hostname):
		self.dstHostname = hostname
	def addSwitchport(self, updatePort):
		self.switchport = updatePort
	def clear(self):
		self.switchHostname = ''
		self.dstHostname = ''
		self.switchport = ''

def getLocalCDPInfo(baseRouter):
	cdpdiscovery = subprocess.check_output(["cdpr", "-d", "eth0"])
	cdpList = string.split(cdpdiscovery,'\n')
	cdpValues = [s for s in cdpList if re.search('value', s)]
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.replace(" ", "")
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.partition(':')[2]
	baseRouter.addHostname(cdpValues[0])
	baseRouter.addIpAddress(cdpValues[1])
	deviceCapability = getCapabilities(baseRouter)
	baseRouter.addCapability(deviceCapability)
	return baseRouter

def getCDPHostnames(router):
	hostnameOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.6"])
	hostnameOutput = string.split(hostnameOutput, '\n')
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.replace('"', '')
	hostnameOutput = filter(None, hostnameOutput)
	return hostnameOutput

def getCapabilities(router):
	capabilityOutput = subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.2.1.4.1"])
	if "forwarding(1)" in capabilityOutput:
		deviceCapability = 'Router'
	else:
		deviceCapability = 'Switch'
	return deviceCapability

def getCDPIPs(router):
	ipAddressOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.4"])
	ipAddressOutput = string.split(ipAddressOutput, '\n')
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val.partition("STRING: ")[2]
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val[:-1]
	ipAddressOutput = filter(None, ipAddressOutput)
	for idx, val in enumerate(ipAddressOutput):
		firstOct = str(int(ipAddressOutput[idx][:2], 16))
		secondOct = str(int(ipAddressOutput[idx][3:5], 16))
		thirdOct = str(int(ipAddressOutput[idx][6:8], 16))
		fourthOct = str(int(ipAddressOutput[idx][9:11], 16))
		ipAddress = firstOct + '.' + secondOct + '.' + thirdOct + '.' + fourthOct
		ipAddressOutput[idx] = ipAddress
	return ipAddressOutput

def getCDPDstInterfaces(router):
	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	interfaceOutput = string.split(interfaceOutput, '\n')
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.replace('"', '')
	interfaceOutput = filter(None, interfaceOutput)
	return interfaceOutput

def getCdpSrcInterfaces(router):
	localIntIDList = subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.2.1.2.2.1.2"])
	localIntList = localIntIDList
	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	intDict = {}
	localIntIDList = string.split(localIntIDList, '\n')
	for idx, val in enumerate(localIntIDList):
		localIntIDList[idx] = val.partition('ifDescr')[2]
	for idx, val in enumerate(localIntIDList):
		localIntIDList[idx] = val.partition(' =')[0]
	localIntIDList = filter(None, localIntIDList)
	localIntList = string.split(localIntList, '\n')
	for idx, val in enumerate(localIntList):
		localIntList[idx] = val.partition('STRING: ')[2]
	localIntList = filter(None, localIntList)
	for idx, val in enumerate(localIntIDList):
		intDict[localIntIDList[idx]] = localIntList[idx]
	interfaceOutput = string.split(interfaceOutput, '\n')
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.partition('9.9.23.1.2.1.1.7')[2]
	for idx, val in enumerate(interfaceOutput):
		searchInt = re.findall(r'^\.[0-9]+', interfaceOutput[idx])
		try:
			interfaceOutput[idx] = (searchInt[0])
		except:
			pass
	interfaceOutput = filter(None, interfaceOutput)
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = intDict[val]
	return interfaceOutput
	
def updateRouters(updateRouter):
	routerHosts = getCDPHostnames(updateRouter)
	routerIPs = getCDPIPs(updateRouter)
	for idx, val in enumerate(routerHosts):
		routerExists = False
		for routerIDX, routerVal in enumerate(topology.routerList):
			if val == routerVal.hostname:
				routerExists = True
				print 'Router Exists'
		if routerExists == False:
			print 'Adding ' + routerHosts[idx]
			newRouter = router([])
			newRouter.addHostname(routerHosts[idx])
			newRouter.addIpAddress(routerIPs[idx])
			deviceCapability = getCapabilities(newRouter)
			newRouter.addCapability(deviceCapability)
			hostnameList = getCDPHostnames(newRouter)
			IPAddressList = getCDPIPs(newRouter)
			dstInterfaceList = getCDPDstInterfaces(newRouter)
			srcInterfaceList = getCdpSrcInterfaces(newRouter)
			for idx, val in enumerate(hostnameList):
				newCDP = cdpEntry([])
				newCDP.addHostname(hostnameList[idx])
				newCDP.addIpAddress(IPAddressList[idx])
				newCDP.addSrcPort(srcInterfaceList[idx])
				newCDP.addDstPort(dstInterfaceList[idx])
				newRouter.addCdpEntry(newCDP)
			topology.addRouter(newRouter)
			updateRouters(newRouter)

def formatInterfaces(topology):
	#Account for 0/0/0 etc.
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
		#TODO: Prioritise Gigabit interfaces over Fa and Se
		# Idea: Three lists for each int type which is the combined?
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

def sortCDPInterfaces(topology):
	for routerIDX, routerVal in enumerate(topology.routerList):
		routerVal.cdp_entries.sort(key=operator.attrgetter('srcPort'))

def findSwitches(topology):
	print 'Looking for switches'
	switchList = []
	for routerIDX, routerVal in enumerate(topology.routerList):
		seen = set()
		uniq = []
		dupes = []
		for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
			if cdpVal.srcPort not in seen:
				uniq.append(cdpVal.srcPort)
				seen.add(cdpVal.srcPort)
			else:
				dupes.append(cdpVal.srcPort)
		set(dupes)

		if len(dupes) > 0:
			switchUpdates = []
			newSwitch = router([])
			switchHostname = 'SW' + str(len(switchList)+1)
			newSwitch.addHostname(switchHostname)
			newSwitch.addCapability('switch')
			portUpdate = switchUpdate([])
			portUpdate.addswitchHostname(switchHostname)
			portUpdate.adddstHostname(routerVal.hostname)
			portUpdate.addSwitchport(dupes[0])
			switchUpdates.append(portUpdate)

			for dupeIDX, dupeInterface in enumerate(dupes):	
				if dupeIDX > 0:
					for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
						if cdpVal.srcPort == dupeInterface:
							endUpdate = switchUpdate([])
							portUpdate.addswitchHostname(switchHostname)
							portUpdate.adddstHostname(routerVal.hostname)
							endUpdate.addSwitchport(cdpVal.dstPort)
							switchUpdates.append(copy.copy(endUpdate))
							endUpdate.clear()
			for updateIDX, updateVal in enumerate(switchUpdates):
				switchCDP = cdpEntry([])
				switchCDP.addHostname(updateVal.dstHostname)
				switchCDP.addSrcPort(switchHostname)
				switchCDP.addDstPort(updateVal.switchport)
				newSwitch.addCdpEntry(copy.copy(switchCDP))
		updateSwitchLinks(topology, switchUpdates, switchHostname)

def updateSwitchLinks(topology, switchUpdates, switchHostname):
	print 'Called'
	interfaceValue = 0
	for value in switchUpdates:
		for routerIDX, routerVal in enumerate(topology.routerList):
			for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
				if ((routerVal.hostname == value.dstHostname) and (cdpVal.srcPort == value.switchport)):
					topology.routerList[routerIDX].removeCDPEntry(cdpVal.srcPort)
					print 'Deleted: ' + routerVal.hostname + ' port: ' + value.switchport
					switchCDP = cdpEntry([])
					switchCDP.addHostname(switchHostname)
					switchCDP.addSrcPort(value.switchport)
					switchCDP.addDstPort(str(interfaceValue))
					topology.routerList[routerIDX].addCdpEntry(copy.copy(switchCDP))
					interfaceValue+=1
	
def createJSON(topology):
	jsonTopology = jsonObject([])
	routerNumber= {}
	for idx, val in enumerate(topology.routerList):
		routerNumber[val.hostname] = idx
	for idx, val in enumerate(topology.routerList):
		nodeDict = {}
		nodeDict['deviceType'] = val.capabilities
		nodeDict['hostname'] = val.hostname
		nodeDict['deviceNo'] = idx
		for cdpIDX, cdpVal in enumerate(val.cdp_entries):
			linksDict = {}
			linksDict['srcRouter'] = val.hostname
			linksDict['srcPort'] = cdpVal.srcPort
			linksDict['source'] = routerNumber[val.hostname]
			linksDict['dstRouter'] = cdpVal.hostname
			linksDict['target'] = routerNumber[cdpVal.hostname]
			linksDict['dstPort'] = cdpVal.dstPort
			linksDict['value'] = 1
			jsonTopology.appendLink(linksDict)
		jsonTopology.appendNode(nodeDict)
	#jsonOutput = json.dumps(vars(jsonTopology),indent=4)
	with open('topology.json', 'w') as outfile:
		json.dump(vars(jsonTopology), outfile,indent=4)
		#json.dump(jsonOutput, outfile,ensure_ascii=False)

if __name__ == "__main__":
	topology = routerList([])
	baseRouter = router([])
	getLocalCDPInfo(baseRouter)	
	hostnameList = getCDPHostnames(baseRouter)
	IPAddressList = getCDPIPs(baseRouter)
	dstInterfaceList = getCDPDstInterfaces(baseRouter)
	srcInterfaceList = getCdpSrcInterfaces(baseRouter)

	for idx, val in enumerate(hostnameList):
		newCDP = cdpEntry([])
		newCDP.addHostname(hostnameList[idx])
		newCDP.addIpAddress(IPAddressList[idx])
		newCDP.addSrcPort(srcInterfaceList[idx])
		newCDP.addDstPort(dstInterfaceList[idx])
		baseRouter.addCdpEntry(newCDP)
	topology.addRouter(baseRouter)
	updateRouters(baseRouter)
	pickle.dump(topology, open("topologyData.p", "wb"))
	formatInterfaces(topology)
	sortCDPInterfaces(topology)
	
	findSwitches(topology)

	for routerIDX, routerVal in enumerate(topology.routerList):
		print routerVal.hostname
		for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
			print cdpVal.hostname + ' on ' + cdpVal.srcPort + ' to ' + cdpVal.dstPort
	
	pickle.dump(topology, open("simulationTopology.p", "wb"))
	createJSON(topology)
	routerDict = {}
	for j, routerVal in enumerate(topology.routerList):
		routerDict[routerVal.hostname] = routerVal.ipAddress
	print routerDict
	pickle.dump(routerDict, open("routerDictionary.p", "wb"))
	with pysftp.Connection('178.62.24.178', username='sftp', private_key='/home/rob/.ssh/id_rsa') as sftp:
		with sftp.cd('json-files'):
			sftp.put('topology.json')