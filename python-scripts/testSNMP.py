import os
import subprocess

class routerList(object):
	def __init__(self, routerList):
		self.routerList = []

	def addRouter(self, routerEntry):
		self.routerList.append(routerEntry)

class router(object):
	def __init__(self, cdp_entries):
		self.cdp_entries = []

	def add_cdp_entry(self, cdp_entry):
		self.cdp_entries.append(cdp_entry)

if __name__ == "__main__":
	topology = routerList([])
	ex_cdp_entry={'hostname': 'R2', 'src_port': 'Fa0/0', 'dest_port': 'Fa0/0', 'ip_address':'172.30.0.1'}
	test_router = router([])
	test_router.add_cdp_entry(ex_cdp_entry)
	topology.addRouter(test_router)
	print topology.routerList[0].cdp_entries

	text = subprocess.check_output(["cdpr", "-d", "eth0"])
	print text


#f=os.popen("snmpwalk -v 2c -c public 172.30.0.1 1.3.6.1.4.1.9.9.23.1.2.1.1.6")
#for i in f.readlines():
#	print "line:", i,
