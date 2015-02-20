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

	def addCdpEntry(self, cdp_entry):
		self.cdp_entries.append(cdp_entry)

	def addHostname(self, hostname):
		self.hostname = hostname

	def addIpAddress(self, ipAddress):
		self.ipAddress = ipAddress

class cdpEntry(object):
	def __init__(self, hostname):
		self.hostname = ''
		self.type = ''
		self.srcPort = ''
		self.ipAddress = ''


if __name__ == "__main__":
	topology = routerList([])

	cdpdiscovery = subprocess.check_output(["cdpr", "-d", "eth0"])
	cdpList = string.split(cdpdiscovery,'\n')
	cdpValues = [s for s in cdpList if re.search('value', s)]
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.replace(" ", "")
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.partition(':')[2]
	baseRouter = router([])
	baseRouter.addHostname(cdpValues[0])
	baseRouter.addIpAddress(cdpValues[1])
	topology.addRouter(baseRouter)

	print baseRouter.hostname
	print baseRouter.ipAddress
	hostnameOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", baseRouter.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.6"])
	hostnameOutput = string.split(hostnameOutput, '\n')
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(hostnameOutput):
		hostnameOutput[idx] = val.replace('"', '')
	hostnameOutput = filter(None, hostnameOutput)
	print hostnameOutput
	
	ipAddressOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", baseRouter.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.4"])
	ipAddressOutput = string.split(ipAddressOutput, '\n')
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val.partition("STRING: ")[2]
	for idx, val in enumerate(ipAddressOutput):
		ipAddressOutput[idx] = val[:-1]
	ipAddressOutput = filter(None, ipAddressOutput)

	firstOct = str(int(ipAddressOutput[0][:2], 16))
	secondOct = str(int(ipAddressOutput[0][3:5], 16))
	thirdOct = str(int(ipAddressOutput[0][6:8], 16))
	fourthOct = str(int(ipAddressOutput[0][9:11], 16))
	ipAddress = firstOct + '.' + secondOct + '.' + thirdOct + '.' + fourthOct
	ipAddressOutput[0] = ipAddress

	firstOct = str(int(ipAddressOutput[1][:2], 16))
	secondOct = str(int(ipAddressOutput[1][3:5], 16))
	thirdOct = str(int(ipAddressOutput[1][6:8], 16))
	fourthOct = str(int(ipAddressOutput[1][9:11], 16))
	ipAddress = firstOct + '.' + secondOct + '.' + thirdOct + '.' + fourthOct
	ipAddressOutput[1] = ipAddress

	print ipAddressOutput

	interfaceOutput=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", baseRouter.ipAddress, ".1.3.6.1.4.1.9.9.23.1.2.1.1.7"])
	interfaceOutput = string.split(interfaceOutput, '\n')
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.partition('"')[2]
	for idx, val in enumerate(interfaceOutput):
		interfaceOutput[idx] = val.replace('"', '')
	interfaceOutput = filter(None, interfaceOutput)
	print interfaceOutput

	for index in len(hostnameOutput):
