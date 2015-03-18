import pickle
from lxml import etree

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

if __name__ == "__main__":
	topology = pickle.load(open('simulationTopology.p', 'rb'))
	routerList = pickle.load(open('routerDictionary.p', 'rb'))

	deviceIndex = {}

	XSI = 'http://www.w3.org/2001/XMLSchema-instance'
	XMLNS = 'http://www.cisco.com/VIRL'
	SCHEMA = 'http://www.cisco.com/VIRL https://raw.github.com/CiscoVIRL/schema/v0.8/virl.xsd'
	nsm = {None: XMLNS, 'xsi': XSI}

	xmlDef = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
	
	topology = etree.Element('topology',attrib={'{' + XSI + '}schemaLocation' : SCHEMA}, nsmap=nsm)
	topology.attrib['schemaVersion'] = '0.8'
	topology.attrib['simulationEngine']='OPENSTACK'

	extensions = etree.Element('extensions')

	managementNet = etree.Element('entry')
	managementNet.attrib["key"] = 'management_network'
	managementNet.attrib["type"] = 'string'
	managementNet.text = "exclusive"
	
	onepkEnable = etree.Element('entry')
	onepkEnable.attrib['key'] = "enable_OnePK"
	onepkEnable.attrib['type'] = 'Boolean'
	onepkEnable.text = 'true'

	cdpEnable = etree.Element('entry')
	cdpEnable.attrib['key'] = 'enable_cdp'
	cdpEnable.attrib['type'] = 'Boolean'
	cdpEnable.text = 'true'

	extensions.append(managementNet)
	extensions.append(onepkEnable)
	extensions.append(cdpEnable)
	topology.append(extensions)

	output = etree.tostring(topology, pretty_print = True)

	print output

	index = 0
	for key, val in routerList.iteritems():
		deviceIndex[index] = key
		index+=1

	print deviceIndex

	print routerList