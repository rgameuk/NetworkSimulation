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
		self.dstPort = ''
		self.ipAddress = ''


if __name__ == "__main__":
	topology = routerList([])
	#ex_cdp_entry={'hostname': 'R2', 'src_port': 'Fa0/0', 'dest_port': 'Fa0/0', 'ip_address':'172.30.0.1'}
	#test_router = router([])
	#test_router.add_cdp_entry(ex_cdp_entry)
	#topology.addRouter(test_router)
	#print topology.routerList[0].cdp_entries

	cdpdiscovery = subprocess.check_output(["cdpr", "-d", "eth0"])
	cdpList = string.split(cdpdiscovery,'\n')
	cdpValues = [s for s in cdpList if re.search('value', s)]
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.replace(" ", "")
	for idx, val in enumerate(cdpValues):
		cdpValues[idx] = val.partition(':')[2]
	print cdpValues
	baseRouter = router([])
	baseRouter.addHostname(cdpValues[0])
	baseRouter.addIpAddress(cdpValues[1])
	topology.addRouter(baseRouter)

	print baseRouter.hostname
	print baseRouter.ipAddress
	f=subprocess.check_output(["snmpwalk", "-v", "2c", "-c", "public", baseRouter.ipAddress, "1.3.6.1.4.1.9.9.23.1.2.1.1.6"])
	print f
	#for i in f.readlines():
	#	print "line:", i,
