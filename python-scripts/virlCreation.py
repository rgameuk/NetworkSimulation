import pickle
from lxml import etree
import random
import collections
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
		self.device = ''
		self.deviceID = ''
		self.ports = collections.OrderedDict()

	def addDevice(self, hostname, id):
		self.device = hostname
		self.deviceID = id
	def addInterface(self, interface, id):
		self.ports[interface] = id

class deviceIDsList(object):
	def __init__(self, deviceList):
		self.deviceList = []

	def addDevice(self, deviceEntry):
		self.deviceList.append(deviceEntry)

class deviceConnection(object):
	def __init__(self, sourceDevice):
		self.sourceDevice = sourceDevice
		self.sourceInterface = ''
		self.destDevice = ''
		self.destInterface = ''

	def addConnection(self, inSourceInterface, inDestDevice, inDestInterface):
		self.sourceInterface = inSourceInterface
		self.destDevice = inDestDevice
		self.destInterface = inDestInterface

class connectionsList(object):
	def __init__(self, connections):
		self.connections = []

	def addConnection(self, deviceConnection):
		self.connections.append(deviceConnection)

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
		if routerVal.capabilities == 'Router':
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
					interfaceEntry = etree.Element('interface')
					interfaceEntry.attrib['id'] = str(intIndex)
					interfaceEntry.attrib['name'] = cdpVal.srcPort
					newNode.append(interfaceEntry)
					intIndex += 1
			topology.append(newNode)
			routerIndexes.addDevice(routerIndex)
		elif routerVal.capabilities == 'switch':
			newNode = etree.Element('node')
			newNode.attrib['name'] = routerVal.hostname
			newNode.attrib['type'] = 'SEGMENT'
			newNode.attrib['location'] = str(random.randrange(0,500)) + ","  + str(random.randrange(0,500))
			topology.append(newNode)
			routerIndexes.addDevice(routerIndex)

	with open ("virlServerEntry.p", "r") as f:
		serverInfo=f.read()

	serverEntry = etree.Element('node')
	serverEntry.attrib['name'] = 'virl-sim-server'
	serverEntry.attrib['type'] = 'SIMPLE'
	serverEntry.attrib['subtype'] = 'server'
	serverEntry.attrib['location'] = str(random.randrange(0,500)) + ","  + str(random.randrange(0,500))
	serverExt = etree.Element('extensions')
	configEntry = etree.Element('entry')
	configEntry.attrib['key'] = 'AutoNetkit.server_username'
	configEntry.attrib['type'] = 'string'
	configEntry.text = 'cisco'
	serverExt.append(configEntry)
	configEntry.attrib['key'] = 'config'
	configEntry.attrib['type'] = 'string'
	configEntry.text = serverInfo
	serverExt.append(configEntry)
	serverEntry.append(serverExt)
	serverIntOne = etree.Element('interface')
	serverIntOne.attrib['id'] = '0'
	serverIntOne.attrib['name'] = 'eth1'
	serverEntry.append(serverIntOne)
	serverIntTwo = etree.Element('interface')
	serverIntTwo.attrib['id'] = '1'
	serverIntTwo.attrib['name'] = 'eth2'
	serverEntry.append(serverIntTwo)
	topology.append(serverEntry)
	snatObject = etree.Element('node')
	snatObject.attrib['name'] = 'snat-1'
	snatObject.attrib['type'] = 'ASSET'
	snatObject.attrib['subtype'] = 'SNAT'
	snatObject.attrib['location'] = str(random.randrange(0,500)) + ","  + str(random.randrange(0,500))
	snatInt = etree.Element('interface')
	snatInt.attrib['id'] = '0'
	snatInt.attrib['name'] = 'link0'
	snatObject.append(snatInt)
	topology.append(snatObject)


	for routerIDX, routerVal in enumerate(deviceTopology.routerList):
		#IDs IN THE CONNECTIONS ARE THE RELATIVE DEFINITION
		if routerVal.capabilities == 'Router':
			for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
				if len(topologyConnections.connections) == 0:
					print 'first connection'
					#add first connection to enable below for loop to run
					newConnectionStore = deviceConnection(routerVal.hostname)
					newConnectionStore.addConnection(cdpVal.srcPort, cdpVal.hostname, cdpVal.dstPort)
					connectionString = '/virl:topology/virl:node['
					#todo: create a fuction to return id for a string
					newConnection = etree.Element('connection')
					srcDevID = ''
					srcIntID = ''
					dstDevID = ''
					dstIntID = ''
					for idIDX, idVal in enumerate(routerIndexes.deviceList):
						#
						if(idVal.device == routerVal.hostname):
							srcDevID = str(idIDX+1)
							intIndex = 1
							for key in idVal.ports:
								if key == cdpVal.srcPort:
									srcIntID = str(intIndex)
								intIndex+=1
						elif(idVal.device == cdpVal.hostname):
							dstDevID = str(idIDX+1)
							intIndex = 1
							for key in idVal.ports:
								if key == cdpVal.dstPort:
									dstIntID = str(intIndex)
								intIndex+=1
					if 'SW' in cdpVal.hostname:
						connectionString+=dstDevID + ']'
					else:
						connectionString+=dstDevID + ']/virl:interface[' + dstIntID + ']'
					newConnection.attrib['dst'] = connectionString 
					connectionString = '/virl:topology/virl:node['
					connectionString += srcDevID + ']/virl:interface[' + srcIntID + ']'
					newConnection.attrib['src'] = connectionString
					topology.append(newConnection)
					topologyConnections.addConnection(newConnectionStore)
					print newConnectionStore.sourceDevice + newConnectionStore.sourceInterface + newConnectionStore.destDevice + newConnectionStore.destInterface
				else:
					connectionFound = False
					for connIDX, connVal in enumerate(topologyConnections.connections):
						if (((connVal.sourceDevice == routerVal.hostname) and (connVal.destDevice == cdpVal.hostname)) or ((connVal.sourceDevice == cdpVal.hostname) and (connVal.destDevice  == routerVal.hostname))):
							#print 'Routers match'
							if (((connVal.sourceInterface == cdpVal.srcPort) and (connVal.destInterface == cdpVal.dstPort)) or (connVal.sourceInterface == cdpVal.dstPort) and (connVal.destInterface == cdpVal.srcPort)):
								#print 'Interfaces match'
								connectionFound = True
								#print 'connection found'
								#print connVal.sourceDevice + connVal.sourceInterface + connVal.destDevice + connVal.destInterface
					if connectionFound == False:
						print 'New connection'
						print 'Connect ' + routerVal.hostname + ' int ' + cdpVal.srcPort +' to ' + cdpVal.hostname + ' int ' + cdpVal.dstPort
						newConnection = etree.Element('connection')
						print routerVal.hostname + cdpVal.srcPort + cdpVal.hostname + cdpVal.dstPort
						newConnectionStore = deviceConnection(routerVal.hostname)
						newConnectionStore.addConnection(cdpVal.srcPort, cdpVal.hostname, cdpVal.dstPort)
						for idIDX, idVal in enumerate(routerIndexes.deviceList):
							if(idVal.device == routerVal.hostname):
								srcDevID = str(idIDX+1)
								intIndex = 1
								for key in idVal.ports:
									if key == cdpVal.srcPort:
										srcIntID = str(intIndex)
									intIndex+=1
							elif(idVal.device == cdpVal.hostname):
								dstDevID = str(idIDX+1)
								intIndex = 1
								for key in idVal.ports:
									if key == cdpVal.dstPort:
										dstIntID = str(intIndex)
									intIndex+=1
						connectionString = '/virl:topology/virl:node['
						if 'SW' in cdpVal.hostname:
							connectionString+=dstDevID + ']'
						else:
							connectionString+=dstDevID + ']/virl:interface[' + dstIntID + ']'
						newConnection.attrib['dst'] = connectionString 
						connectionString = '/virl:topology/virl:node['
						connectionString += srcDevID + ']/virl:interface[' + srcIntID + ']'
						newConnection.attrib['src'] = connectionString
						topology.append(newConnection)
						topologyConnections.addConnection(newConnectionStore)
		elif routerVal.capabilities == 'switch':
			for cdpIDX, cdpVal in enumerate(routerVal.cdp_entries):
				if len(topologyConnections.connections) == 0:
					print 'first connection'
					#add first connection to enable below for loop to run
					newConnectionStore = deviceConnection(routerVal.hostname)
					newConnectionStore.addConnection(cdpVal.srcPort, cdpVal.hostname, cdpVal.dstPort)
					connectionString = '/virl:topology/virl:node['
					#todo: create a fuction to return id for a string
					newConnection = etree.Element('connection')
					srcDevID = ''
					srcIntID = ''
					dstDevID = ''
					dstIntID = ''
					for idIDX, idVal in enumerate(routerIndexes.deviceList):
						if(idVal.device == routerVal.hostname):
							srcDevID = str(idIDX+1)
							intIndex = 1
							for key in idVal.ports:
								if key == cdpVal.srcPort:
									srcIntID = str(intIndex)
								intIndex+=1
						elif(idVal.device == cdpVal.hostname):
							dstDevID = str(idIDX+1)
							intIndex = 1
							for key in idVal.ports:
								if key == cdpVal.dstPort:
									dstIntID = str(intIndex)
								intIndex+=1
					connectionString+=dstDevID + ']/virl:interface[' + dstIntID + ']'
					newConnection.attrib['dst'] = connectionString 
					connectionString = '/virl:topology/virl:node['
					connectionString += srcDevID + ']/virl:interface[' + srcIntID + ']'
					newConnection.attrib['src'] = connectionString
					topology.append(newConnection)
					topologyConnections.addConnection(newConnectionStore)
					print newConnectionStore.sourceDevice + newConnectionStore.sourceInterface + newConnectionStore.destDevice + newConnectionStore.destInterface
				else:
					connectionFound = False
					for connIDX, connVal in enumerate(topologyConnections.connections):
						if (((connVal.sourceDevice == routerVal.hostname) and (connVal.destDevice == cdpVal.hostname)) or ((connVal.sourceDevice == cdpVal.hostname) and (connVal.destDevice  == routerVal.hostname))):
							#print 'Routers match'
							connectionFound = True
								#print 'connection found'
								#print connVal.sourceDevice + connVal.sourceInterface + connVal.destDevice + connVal.destInterface
					if connectionFound == False:
						print 'New connection'
						print 'Connect ' + routerVal.hostname + ' int ' + cdpVal.srcPort +' to ' + cdpVal.hostname + ' int ' + cdpVal.dstPort
						newConnection = etree.Element('connection')
						print routerVal.hostname + cdpVal.srcPort + cdpVal.hostname + cdpVal.dstPort
						newConnectionStore = deviceConnection(routerVal.hostname)
						newConnectionStore.addConnection(cdpVal.srcPort, cdpVal.hostname, cdpVal.dstPort)
						for idIDX, idVal in enumerate(routerIndexes.deviceList):
							if(idVal.device == routerVal.hostname):
								srcDevID = str(idIDX+1)
								intIndex = 1
								for key in idVal.ports:
									if key == cdpVal.srcPort:
										srcIntID = str(intIndex)
									intIndex+=1
							elif(idVal.device == cdpVal.hostname):
								dstDevID = str(idIDX+1)
								intIndex = 1
								for key in idVal.ports:
									if key == cdpVal.dstPort:
										dstIntID = str(intIndex)
									intIndex+=1
						connectionString = '/virl:topology/virl:node['
						connectionString+=dstDevID + ']/virl:interface[' + dstIntID + ']'
						newConnection.attrib['dst'] = connectionString 
						connectionString = '/virl:topology/virl:node['
						connectionString += srcDevID + ']/virl:interface[' + srcIntID + ']'
						newConnection.attrib['src'] = connectionString
						topology.append(newConnection)
						topologyConnections.addConnection(newConnectionStore)

	snatInt = etree.Element('connection')
	destinationString = '/virl:topology/virl:node[' + str(len(deviceTopology.routerList)+2) + ']/virl:interface[1]'
	snatInt.attrib['dst'] = destinationString
	sourceString = '/virl:topology/virl:node[' + str(len(deviceTopology.routerList)+1) + ']/virl:interface[1]'
	snatInt.attrib['src'] = sourceString
	topology.append(snatInt)

	print len(deviceTopology.routerList)

	output = etree.tostring(topology, pretty_print = True)
	with open('topology.virl', 'w') as f:
		f.write(output)
		f.close()
	#print output

	for idx, val in enumerate(topologyConnections.connections):
		print val.sourceDevice + ' connects to ' + val.destDevice

	with pysftp.Connection('178.62.24.178', username='sftp', private_key='/home/rob/.ssh/id_rsa') as sftp:
		with sftp.cd('virl-files'):
			sftp.put('topology.virl')
