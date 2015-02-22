import os
import subprocess
import string
import re

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

class cdpEntry(object):
	def __init__(self, hostname):
		self.hostname = ''
		self.srcPort = ''
		self.ipAddress = ''

	def addHostname(self, hostname):
		self.hostname = hostname

	def addIpAddress(self, ipAddress):
		self.ipAddress = ipAddress

	def addSrcPort(self, srcPort):
		self.srcPort = srcPort

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

def getCDPInterfaces(router):
	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", router.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	interfaceOutput = string.split(interfaceOutput, '\n')
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.replace('"', '')
	interfaceOutput = filter(None, interfaceOutput)
	return interfaceOutput

def addRoutersFromCDP(cdpEntries):
	for idx, val in enumerate(topology.routerList):
		hostnameList = getCDPHostnames(val)
		IPAddressList = getCDPIPs(val)
		InterfaceList = getCDPInterfaces(val)
		for i, discoverVal in enumerate(hostnameList):	#For all new routers
			alreadyKnown = False
			for j, routerVal in enumerate(topology.routerList): #For all stored routers
				if discoverVal == routerVal.hostname:
					alreadyKnown = True		#Does not make an new Router object as one already exists
			if alreadyKnown == False:
				newRouter = router([])
				newRouter.addHostname(hostnameList[i])
				newRouter.addIpAddress(IPAddressList[i])
				topology.addRouter(newRouter)
				deviceCapability = getCapabilities(newRouter)
				newRouter.addCapability(deviceCapability)

if __name__ == "__main__":
	topology = routerList([])
	baseRouter = router([])
	getLocalCDPInfo(baseRouter)	
	hostnameList = getCDPHostnames(baseRouter)
	IPAddressList = getCDPIPs(baseRouter)
	InterfaceList = getCDPInterfaces(baseRouter)

	for idx, val in enumerate(hostnameList):
		newCDP = cdpEntry([])
		newCDP.addHostname(hostnameList[idx])
		newCDP.addIpAddress(IPAddressList[idx])
		newCDP.addSrcPort(InterfaceList[idx])
		baseRouter.addCdpEntry(newCDP)
	topology.addRouter(baseRouter)
	addRoutersFromCDP(baseRouter.cdp_entries)