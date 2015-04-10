# coding=utf-8
import os, requests, sys, json
import telnetlib
import time
import paramiko
from paramikoe import SSHClientInteraction


def setupServer(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress, ipDictionary):
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
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write('sudo chmod 666 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write(nameserverOneCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write(nameserverTwoCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write('sudo chmod 644 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	lineNumber = 3
	for key, val in ipDictionary.iteritems():
		telnet.write('sudo sed -i "' + str(lineNumber) + 'i ' + val + ' ' + key + '" /etc/hosts' + '\n')
		response = telnet.read_until('cisco@virl-sim-server:~$')
		lineNumber +=1
	telnet.close()
	print 'virl-sim-server interfaces updated. Server available @ ' + SNATAddress

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
				ipDictionary[str(hostname)] = str(managementIP)
			if ((devKey == 'NodeName') and (devVal == 'virl-sim-server')):
				serverManIP = rawDeviceInfo['managementIP']
				serverExtIP = rawDeviceInfo['internalAddr']
				SNATAddress = rawDeviceInfo['externalAddr']
				consolePort = rawDeviceInfo['PortConsole']
			if 'lxc-flat.External Address' in key:
				if (devKey == 'managementIP'):
					lxcAddress = devVal
	setupServer(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress, ipDictionary)

