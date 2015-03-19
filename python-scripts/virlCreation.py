import pickle
from lxml import etree
import random

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

class deviceIDs(object):
	def __init__(self, hostname):
		self.device = {}
		self.ports = {}

	def addDevice(self, hostname, id):
		self.device[hostname] = id
	def addInterface(self, interface, id):
		self.ports[interface] = id

class deviceIDsList(object):
	def __init__(self, deviceList):
		self.deviceList = []

	def addRouter(self, deviceEntry):
		self.routerList.append(deviceEntry)

class deviceConnection(object):
	def __init__(self, sourceDevice):
		self.sourceDevice = ''
		self.sourceInterface = ''
		self.destDevice = ''
		self.destInterface = ''

	def addConnection(sourceDevice, sourceInterface, destDevice, destInterface):
		self.sourceDevice = sourceDevice
		self.sourceInterface = sourceInterface
		self.destDevice = destDevice
		self.destInterface = destInterface

class connectionsList(object):
	def __init__(self, connections):
		self.connections = []

	def addConnection(self, deviceConnection):
		self.routerList.append(deviceConnection)

if __name__ == "__main__":
	deviceTopology = pickle.load(open('simulationTopology.p', 'rb'))
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

	routerIndexes = deviceIDsList([])
	topologyConnections = connectionsList([])
	index = 0
		
	for routerIDX, routerVal in enumerate(deviceTopology.routerList):
		routerIndex = deviceIDs([])
		routerIndex.addDevice(routerVal.hostname, index)
		index+=1
		newNode = etree.Element('node')
		newNode.attrib['name'] = routerVal.hostname
		newNode.attrib['type'] = 'SIMPLE'
		newNode.attrib['subtype'] = 'IOSv'
		newNode.attrib['location'] = str(random.randrange(0,500)) + ","  + str(random.randrange(0,500))
		routerExt = etree.Element('extensions')
		configEntry = etree.Element('entry')
		configEntry.attrib['key'] = 'config'
		configEntry.attrib['type'] = 'string'
		with open('./config-files/' + routerVal.hostname.lower() + '.edited', 'r') as f:
			config = f.read()
			f.close()
		configEntry.text = config
		routerExt.append(configEntry)
		newNode.append(routerExt)		
		uniqueInterfaces = []
		intIndex = 0
		for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
			if cdpVal.srcPort not in uniqueInterfaces:
				uniqueInterfaces.append(cdpVal.srcPort)
				routerIndex.addInterface(cdpVal.srcPort, intIndex)
				interfaceEntry = etree.Element('connection')
				interfaceEntry.attrib['id'] = str(intIndex)
				interfaceEntry.attrib['name'] = cdpVal.srcPort
				newNode.append(interfaceEntry)
		topology.append(newNode)

		for cdpIDX, cdpVal in enumerate(routerVal.cdp_enties):
			connectionFound = False
			for val in enumerate(topologyConnections):
				if (((val.sourceDevice == routerVal.hostname) and (val.destDevice == cdpVal.hostname)) or ((val.sourceDevice == cdpVal.hostname) and (val.destDevice  == routerVal.hostname))):
					if (((val.sourceInterface == cdpVal.srcPort) and (val.destInterface == cdpVal.dstPort)) or (val.sourceInterface == cdpVal.dstPort) and (val.destInterface == cdpVal.srcPort)):
						connectionFound = True
				if connectionFound == False:
					newConnection = etree.Element('connection')
					newConnection.attrib['dst'] = '/virl:topology/virl:node[' + 



	output = etree.tostring(topology, pretty_print = True)
	print output
	print deviceIndex

	print routerList
