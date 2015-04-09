import os, requests, sys, json
import telnetlib

def updateServerIP(serverManIP, serverExtIP, virlHost, consolePort, username, password):

	telnet = telnetlib.Telnet(virlHost, int(consolePort))                   

	telnet.write('\n')
	response = telnet.read_until('virl-sim-server login:')
	print response
	telnet.write('cisco'+ '\n')
	response = telnet.read_until('Password:')
	print response
	telnet.write('cisco' + '\n')
	telnet.write('\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write('touch telnet_test.file\n')
	print response
	telnet.close()

if __name__ == "__main__":
	virlHost = "158.125.102.75"
	username = "rob"
	password = "rrr"
	url = "http://virl.lboro.ac.uk:19399/simengine/rest/launch"
	hostsURL = "http://virl.lboro.ac.uk:19399/roster/rest/"
	topology = open('topology.virl', 'r')
	headers = {'content-type': 'text/xml'}
	payload = {'file': 'manual@launch_topo'}

	#result = requests.post(url, auth=(username,password), params=payload, data=topology, headers=headers)
	
	hostInformation = requests.get(hostsURL, auth=(username, password))
	hostJSON = json.loads(hostInformation.text)
	ipDictionary = {}
	serverManIP = ''
	serverExtIP = ''
	SNATAddress = ''
	lxcAddress = ''
	consolePort = '' 

	#May have to investigate a time here as it takes ~ 10 seconds to spawn addresses
	del hostJSON['UUID']

	for key, val in hostJSON.iteritems():
		rawDeviceInfo = val	
		for devKey, devVal in rawDeviceInfo.iteritems():
			if ((devKey == 'NodeSubtype') and (devVal == 'IOSv')):
				hostname = rawDeviceInfo['NodeName']
				managementIP = rawDeviceInfo['managementIP']
				ipDictionary[hostname] = managementIP
			if ((devKey == 'NodeName') and (devVal == 'virl-sim-server')):
				serverManIP = rawDeviceInfo['managementIP']
				serverExtIP = rawDeviceInfo['internalAddr']
				SNATAddress = rawDeviceInfo['externalAddr']
				consolePort = rawDeviceInfo['PortConsole']
			if 'lxc-flat.External Address' in key:
				if (devKey == 'managementIP'):
					lxcAddress = devVal
	updateServerIP(serverManIP, serverExtIP, virlHost, consolePort, username, password)
