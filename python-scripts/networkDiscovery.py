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
import time
import sys
import argparse
import ipaddr 

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
	#Function listens on interface for a CDP packet and creates a router if successful. Script closes if no packet found
	try: #Catches exception generated when CDPR returns null (CDP packet not seen)
		cdpdiscovery = subprocess.check_output(["cdpr", "-d", "eth0", "-t", "61"])
		#Starts subprocess for CDP, timeout is set to 61 as default CDP timer is 60
		#CDP returns the information in lines, below code breaks in into a list and processes the information 
		cdpList = string.split(cdpdiscovery,'\n')
		cdpValues = [s for s in cdpList if re.search('value', s)]
		for idx, val in enumerate(cdpValues):
			cdpValues[idx] = val.replace(" ", "")
		for idx, val in enumerate(cdpValues):
			cdpValues[idx] = val.partition(':')[2]
		#The below code creates a router object for the baserouter and returns it to main
		if checkNetworks == True:
			#Networks ranges have been specified for discovery
			notInNetwork = True
			ipAddress = str(cdpValues[1]) + '/32'
			#Create string to hold device IP address
			for idx, val in enumerate(specifiedNetworks):
				#Check each network that has been specified
				if ipaddr.IPv4Network(ipAddress) in val:
					#Check the ip address of the device is inside the network
					#If it is, create a device for it
					notInNetwork = False
					baseRouter.addHostname(cdpValues[0])
					baseRouter.addIpAddress(cdpValues[1])
					deviceCapability = getCapabilities(baseRouter)
					baseRouter.addCapability(deviceCapability)
					return baseRouter
			if notInNetwork == True:
				#If the device is not in the network, throw an error
				print 'Local device is not in specied networks. Aborting Network Discovery'
				sys.exit()
		else:
			#Networks have not been specified, create an object for the device
			baseRouter.addHostname(cdpValues[0])
			baseRouter.addIpAddress(cdpValues[1])
			deviceCapability = getCapabilities(baseRouter)
			baseRouter.addCapability(deviceCapability)
			return baseRouter
	except:
		#Exception thrown, this will occur when no CDP packet is seen within the timeout of CDPR
		print 'No CDP packet discovered. Aborting Network Discovery'
		sys.exit()
		
def getCDPHostnames(router):
	#Function makes an SNMP call to the device defined by router. It then processes the returned data into a list of Hostnames which is returned to the updateRouters function
	#Makes SNMP call and holds the output in a variable
	hostnameOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.6"])
	#Parse the output until only the IP addresses remain
	hostnameOutput = string.split(hostnameOutput, '\n')
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.replace('"', '')
	hostnameOutput = filter(None, hostnameOutput)
	return hostnameOutput

def getCapabilities(router):
	#Function makes an SNMP call to the device defined by router. Returns whether the device is a router or a switch
	capabilityOutput = subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.2.1.4.1"])
	if "forwarding(1)" in capabilityOutput:
		deviceCapability = 'Router'
	else:
		deviceCapability = 'Switch'
	return deviceCapability

def getCDPIPs(router):
	#Function makes a call to device which returns a list of IP addresses in HEX format, the are converted to decimal and returned as list
	ipAddressOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.4"])
	ipAddressOutput = string.split(ipAddressOutput, '\n')
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val.partition("STRING: ")[2]
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val[:-1]
	ipAddressOutput = filter(None, ipAddressOutput)
	#Converts the Hex octets into binary octets
	for idx, val in enumerate(ipAddressOutput):
		firstOct = str(int(ipAddressOutput[idx][:2], 16))
		secondOct = str(int(ipAddressOutput[idx][3:5], 16))
		thirdOct = str(int(ipAddressOutput[idx][6:8], 16))
		fourthOct = str(int(ipAddressOutput[idx][9:11], 16))
		ipAddress = firstOct + '.' + secondOct + '.' + thirdOct + '.' + fourthOct
		ipAddressOutput[idx] = ipAddress
	return ipAddressOutput

def getCDPDstInterfaces(router):
	#Function makes an SNMP call to the device defined by router. Returns a list of remote interfaces
	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	interfaceOutput = string.split(interfaceOutput, '\n')
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.replace('"', '')
	interfaceOutput = filter(None, interfaceOutput)
	return interfaceOutput

def getCdpSrcInterfaces(router):
	#Function returns a list of local interfaces of connections to the device. 
	#The local interface is contained in the OID of a remote CDP connection. Therefore the local interface ID needs to be found first
	localIntIDList = subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.2.1.2.2.1.2"])
	localIntList = localIntIDList
	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	intDict = {}
	#Partition the local interface information until the interface IDs remain
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
	#Partition the remote interfaces until the ID for the local interface is obtained
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
	
def updateRouters(updateRouter, topology):
	routerHosts = getCDPHostnames(updateRouter)
	routerIPs = getCDPIPs(updateRouter)
	#For each connected device to the update Router
	for idx, val in enumerate(routerHosts):
		routerExists = False
		for routerIDX, routerVal in enumerate(topology.routerList):
			#Check whether the device already exists
			if val == routerVal.hostname:
				routerExists = True
		if routerExists == False:
			#If the device is not already known
			if checkNetworks == True:
				#If there is a specified network set
				ipAddress = routerIPs[idx] + '/32'
				deviceAdded = False
				#Check if device is within the specified subnets
				for specIDX, specVal in enumerate(specifiedNetworks):
					if ipaddr.IPv4Network(ipAddress) in specVal:
						if deviceAdded == False:
							#Create the device
							newRouter = router([])
							newRouter.addHostname(routerHosts[idx])
							newRouter.addIpAddress(routerIPs[idx])
							try:
								deviceCapability = getCapabilities(newRouter)
								newRouter.addCapability(deviceCapability)
								hostnameList = getCDPHostnames(newRouter)
								IPAddressList = getCDPIPs(newRouter)
								dstInterfaceList = getCDPDstInterfaces(newRouter)
								srcInterfaceList = getCdpSrcInterfaces(newRouter)
								for newIDX, newVal in enumerate(hostnameList):
									#Checks that the connected interfaces to the device fall within the defined subnets, if they do not, ignore them
									newIPAddress = IPAddressList[newIDX] + '/32'
									deviceAdded = False
									for newSpecIDX, newSpecVal in enumerate(specifiedNetworks):
										if ipaddr.IPv4Network(newIPAddress) in newSpecVal:
											if deviceAdded == False:
												newCDP = cdpEntry([])
												newCDP.addHostname(hostnameList[newIDX])
												newCDP.addIpAddress(IPAddressList[newIDX])
												newCDP.addSrcPort(srcInterfaceList[newIDX])
												newCDP.addDstPort(dstInterfaceList[newIDX])
												newRouter.addCdpEntry(newCDP)
												deviceAdded = True
								print 'Adding ' + routerHosts[idx]
								topology.addRouter(newRouter)
								updateRouters(newRouter, topology)
							except:
								#Exception thrown - device is unresponsive to SNMP
								unresponsiveDevices.append(routerHosts[idx])
			else:
				#All networks are to be included. Add the device
				try:
					newRouter = router([])
					newRouter.addHostname(routerHosts[idx])
					newRouter.addIpAddress(routerIPs[idx])
					deviceCapability = getCapabilities(newRouter)
					newRouter.addCapability(deviceCapability)
					hostnameList = getCDPHostnames(newRouter)
					IPAddressList = getCDPIPs(newRouter)
					dstInterfaceList = getCDPDstInterfaces(newRouter)
					srcInterfaceList = getCdpSrcInterfaces(newRouter)
					for newIDX, newVal in enumerate(hostnameList):
						#Add each interface to the device
						newCDP = cdpEntry([])
						newCDP.addHostname(hostnameList[newIDX])
						newCDP.addIpAddress(IPAddressList[newIDX])
						newCDP.addSrcPort(srcInterfaceList[newIDX])
						newCDP.addDstPort(dstInterfaceList[newIDX])
						newRouter.addCdpEntry(newCDP)
					#add the new device to the topology
					print 'Adding ' + routerHosts[idx]
					topology.addRouter(newRouter)
					updateRouters(newRouter, topology)
				except:
					#Exception thrown - device is unresponsive to SNMP
					unresponsiveDevices.append(routerHosts[idx])

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

def sortCDPInterfaces(topology):
	for routerIDX, routerVal in enumerate(topology.routerList):
		routerVal.cdp_entries.sort(key=operator.attrgetter('srcPort'))

def findSwitches(topology):
	print 'Looking for switches'
	switchList = []
	switchID = 1
	for routerIDX, routerVal in enumerate(topology.routerList):
		if routerVal.capabilities == 'Router':
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
				for dupeIDX, dupeInterface in enumerate(dupes):
					switchUpdates = []	
					newSwitch = router([])
					switchHostname = 'SW' + str(switchID)
					newSwitch.addHostname(switchHostname)
					newSwitch.addCapability('switch')
					localUpdate = switchUpdate([])
					localUpdate.addswitchHostname(switchHostname)
					localUpdate.adddstHostname(routerVal.hostname)
					localUpdate.addSwitchport(dupeInterface)
					switchUpdates.append(localUpdate)
					#if dupeIDX > 0:
					for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
						if cdpVal.srcPort == dupeInterface:
							endUpdate = switchUpdate([])
							endUpdate.addswitchHostname(switchHostname)
							endUpdate.adddstHostname(cdpVal.hostname)
							endUpdate.addSwitchport(cdpVal.dstPort)
							switchUpdates.append(copy.copy(endUpdate))
							endUpdate.clear()
					switchExists = False
					for deviceIDX, deviceVal in enumerate(topology.routerList):
						if deviceVal.hostname == switchHostname:
							switchExists = True
					if switchExists == False:
						topology.addRouter(newSwitch)
						switchList.append(newSwitch.hostname)
						switchID+=1
				#for val in switchUpdates:
				#	print val.switchHostname + val.dstHostname + val.switchport
					for updateIDX, updateVal in enumerate(switchUpdates):
						switchCDP = cdpEntry([])
						switchCDP.addHostname(updateVal.dstHostname)
						switchCDP.addSrcPort(str(updateIDX))
						switchCDP.addDstPort(updateVal.switchport)
						newSwitch.addCdpEntry(copy.copy(switchCDP))
					updateSwitchLinks(topology, switchUpdates, switchHostname)

def updateSwitchLinks(topology, switchUpdates, switchHostname):
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
		nodeDict['ipAddress'] = val.ipAddress
		nodeDict['deviceNo'] = idx
		for cdpIDX, cdpVal in enumerate(val.cdp_entries):
			linksDict = {}
			linksDict['srcRouter'] = val.hostname
			linksDict['srcPort'] = cdpVal.srcPort
			linksDict['source'] = routerNumber[val.hostname]
			linksDict['dstRouter'] = cdpVal.hostname
			linksDict['target'] = routerNumber[cdpVal.hostname]
			linksDict['dstPort'] = cdpVal.dstPort
			linksDict['dstIpAddress'] = cdpVal.ipAddress
			linksDict['value'] = 1
			jsonTopology.appendLink(linksDict)
		jsonTopology.appendNode(nodeDict)
	#jsonOutput = json.dumps(vars(jsonTopology),indent=4)
	with open('topology.json', 'w') as outfile:
		json.dump(vars(jsonTopology), outfile,indent=4)
		#json.dump(jsonOutput, outfile,ensure_ascii=False)

def getUserInput():
	networkInput = ''
	subnetInput = ''
	print 'Enter the network address at the first prompt, followed by the subnet at the second. Type "end" to finish'
	while networkInput != 'end':
		print 'Enter the network address:'
		networkInput = raw_input()
		if networkInput != 'end':
			print 'Enter the subnet mask in CIDR notation (Example: /24)'
			subnetInput = raw_input()
			try:
				newIP = ipaddr.IPv4Network(networkInput+subnetInput, strict=True)
				specifiedNetworks.append(newIP)
			except:
				print 'Invalid IP Network'

def removeUnresponsive(topology):
	#Function removes links with reference to unresponsive devices from the topology
	#Uses set() to create a list of unique entries
	deviceDelete = set(unresponsiveDevices)
	#For every unresponsive device:
	for idx, val in enumerate(deviceDelete):
		print 'Could not communicate with ' + val + ' it will be removed from the topology'
		#For every device in the topology
		for deviceIDX, deviceVal in enumerate(topology.routerList):
			#For all of the above devices CDP entries (links)
			for cdpIDX, cdpVal in enumerate(deviceVal.cdp_entries):
				#If the link connects to the unresponsve device, remove it from the topology
				if cdpVal.hostname == val:
					print 'Removing ' + cdpVal.srcPort + ' from ' + deviceVal.hostname
					deviceVal.removeCDPEntry(cdpVal.srcPort)


def main():
	global checkNetworks
	global specifiedNetworks
	global unresponsiveDevices
	unresponsiveDevices = []
	checkNetworks = False
	parser = argparse.ArgumentParser()
	parser.add_argument("--specify", help="Specify the networks to be discovered",
                    action="store_true")
	args = parser.parse_args()
	if args.specify:
		specifiedNetworks = []
		checkNetworks = True
		getUserInput()
		print specifiedNetworks

	topology = routerList([])
	baseRouter = router([])
	getLocalCDPInfo(baseRouter)	
	hostnameList = getCDPHostnames(baseRouter)
	IPAddressList = getCDPIPs(baseRouter)
	dstInterfaceList = getCDPDstInterfaces(baseRouter)
	srcInterfaceList = getCdpSrcInterfaces(baseRouter)

	for idx, val in enumerate(IPAddressList):
		if checkNetworks == True:
			ipAddress = val + '/32'
			deviceAdded = False
			for specIDX, specVal in enumerate(specifiedNetworks):
				if ipaddr.IPv4Network(ipAddress) in specVal:
					if deviceAdded == False:
						newCDP = cdpEntry([])
						newCDP.addHostname(hostnameList[idx])
						newCDP.addIpAddress(IPAddressList[idx])
						newCDP.addSrcPort(srcInterfaceList[idx])
						newCDP.addDstPort(dstInterfaceList[idx])
						baseRouter.addCdpEntry(newCDP)
						deviceAdded = True
		else:
			newCDP = cdpEntry([])
			newCDP.addHostname(hostnameList[idx])
			newCDP.addIpAddress(IPAddressList[idx])
			newCDP.addSrcPort(srcInterfaceList[idx])
			newCDP.addDstPort(dstInterfaceList[idx])
			baseRouter.addCdpEntry(newCDP)
	topology.addRouter(baseRouter)
	updateRouters(baseRouter, topology)
	if len(unresponsiveDevices) > 0:
		removeUnresponsive(topology)
	pickle.dump(topology, open("topologyData.p", "wb"))
	formatInterfaces(topology)
	findSwitches(topology)
	sortCDPInterfaces(topology)
	for routerIDX, routerVal in enumerate(topology.routerList):
		print routerVal.hostname
		for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
			print cdpVal.hostname + ' on ' + cdpVal.srcPort + ' to ' + cdpVal.dstPort
	
	pickle.dump(topology, open("simulationTopology.p", "wb"))
	createJSON(topology)
	routerDict = {}
	for j, routerVal in enumerate(topology.routerList):
		if routerVal.capabilities == 'Router':
			routerDict[routerVal.hostname] = routerVal.ipAddress
	print routerDict
	pickle.dump(routerDict, open("routerDictionary.p", "wb"))
	try:
		with pysftp.Connection('178.62.24.178', username='sftp', private_key='/home/rob/.ssh/id_rsa') as sftp:
			with sftp.cd('json-files'):
				sftp.put('topology.json')
	except:
		print 'SSH Key for server is missing from host'

if __name__ == "__main__":
	main()