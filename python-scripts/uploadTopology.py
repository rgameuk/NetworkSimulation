# coding=utf-8
import os, requests, sys, json
import telnetlib
import time


def updateServerIP(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress):
	username = 'cisco'
	password = 'cisco'
	interfaceCommand = 'sudo ifconfig eth1 up '+ serverExtIP + ' netmask 255.255.255.0'
	defaultGWCommand = 'sudo route add default gw 10.254.0.1 eth1'
	nameserverOneCommand = 'sudo echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
	nameserverTwoCommand = 'sudo echo "nameserver 8.8.4.4" >> /etc/resolv.conf'

	telnet = telnetlib.Telnet(virlHost, int(consolePort))                   

	telnet.write('\n')
	response = telnet.read_until('virl-sim-server login:')
	telnet.write(username+ '\n')
	response = telnet.read_until('Password:')
	telnet.write(password + '\n')
	telnet.write('\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write(str(interfaceCommand) + '\n')
	response = telnet.read_until('[sudo] password for cisco:')
	telnet.write(password + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write(defaultGWCommand + '\n')
	#print response
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#print response
	telnet.write('sudo chmod 666 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#print response
	telnet.write(nameserverOneCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#print response
	telnet.write(nameserverTwoCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#print response
	telnet.write('sudo chmod 644 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#print response
	telnet.close()
	print 'virl-sim-server interfaces updated. Server available @ ' + SNATAddress

def addDeviceAccounts(virlHost, devicePortDict):
	username = 'cisco'
	password = 'cisco'
	enablePassword = 'cisco'
	accountCommand = 'username ' + username + ' password ' + password
	enableCommand = 'enable password ' + enablePassword
	
	for key, val in devicePortDict.iteritems():
		print key, val
		telnet = telnetlib.Telnet(virlHost, val)             
		telnet.write('\n')
		response = telnet.read_until(key+'#')
		print response
		telnet.write('configure terminal'+ '\n')
		response = telnet.read_until(key + '(config)#')
		print response
		telnet.write(accountCommand + '\n')
		response = telnet.read_until(key + '(config)#')
		telnet.write(enableCommand + '\n')
		response = telnet.read_until(key + '(config)#')
		telnet.write('end' + '\n')
		response = telnet.read_until(key+'#')
		print response
		telnet.write('write memory' + '\n')
		#response = telnet.read_until(key+'#')
		#print response
		telnet.close()
	print 'Accounts added to devices'
	print 'Username: ' + username
	print 'Password: ' + password

if __name__ == "__main__":
	virlHost = "158.125.102.75"
	username = "rob"
	password = "rrr"
	url = "http://virl.lboro.ac.uk:19399/simengine/rest/launch"
	hostsURL = "http://virl.lboro.ac.uk:19399/roster/rest/"
	topology = open('topology.virl', 'r')
	headers = {'content-type': 'text/xml'}
	payload = {'file': 'manual@launch_topo'}

	result = requests.post(url, auth=(username,password), params=payload, data=topology, headers=headers)
	print 'Waiting for simulation launch'
	time.sleep(45) #Required as it takes time for ip addresses to be generated
	print 'Gathering simulation information'
	hostInformation = requests.get(hostsURL, auth=(username, password))
	hostJSON = json.loads(hostInformation.text)
	ipDictionary = {}
	devicePortDict = {}
	serverManIP = ''
	serverExtIP = ''
	SNATAddress = ''
	lxcAddress = ''
	consolePort = ''
	deviceConsolePort = '' 

	#May have to investigate a time here as it takes ~ 10 seconds to spawn addresses
	del hostJSON['UUID']

	for key, val in hostJSON.iteritems():
		rawDeviceInfo = val	
		for devKey, devVal in rawDeviceInfo.iteritems():
			if ((devKey == 'NodeSubtype') and (devVal == 'IOSv')):
				hostname = rawDeviceInfo['NodeName']
				managementIP = rawDeviceInfo['managementIP']
				deviceConsolePort = rawDeviceInfo['managementIP']
				ipDictionary[str(hostname)] = str(managementIP)
				deviceConsolePort = rawDeviceInfo['PortConsole']
				print deviceConsolePort
				devicePortDict[str(hostname)] = int(deviceConsolePort)
			if ((devKey == 'NodeName') and (devVal == 'virl-sim-server')):
				serverManIP = rawDeviceInfo['managementIP']
				serverExtIP = rawDeviceInfo['internalAddr']
				SNATAddress = rawDeviceInfo['externalAddr']
				consolePort = rawDeviceInfo['PortConsole']
			if 'lxc-flat.External Address' in key:
				if (devKey == 'managementIP'):
					lxcAddress = devVal
	print devicePortDict
	updateServerIP(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress)
	#addDeviceAccounts(virlHost, devicePortDict)
