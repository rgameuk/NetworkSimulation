# coding=utf-8
import os, requests, sys, json
import telnetlib
import time


def setupServer(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress, ipDictionary):
	#Function uses telnet to log into and configure virl-sim-server using a python expect module
	username = 'cisco'
	password = 'cisco'
	interfaceCommand = 'sudo ifconfig eth1 up '+ serverExtIP + ' netmask 255.255.255.0'
	defaultGWCommand = 'sudo route add default gw 10.254.0.1 eth1'
	nameserverOneCommand = 'sudo echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
	nameserverTwoCommand = 'sudo echo "nameserver 8.8.4.4" >> /etc/resolv.conf'

	#Create connection to 
	telnet = telnetlib.Telnet(virlHost, int(consolePort))                   

	#Send a return key to bring up stdout
	telnet.write('\n')
	#Use expect to log in to server
	response = telnet.read_until('virl-sim-server login:')
	telnet.write(username+ '\n')
	response = telnet.read_until('Password:')
	telnet.write(password + '\n')
	telnet.write('\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#Send interface command to set eth1 to public ip address
	#Elevate privileges to superuser
	telnet.write(str(interfaceCommand) + '\n')
	response = telnet.read_until('[sudo] password for cisco:')
	telnet.write(password + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#Set server default gateway to SNAT object
	telnet.write(defaultGWCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#Set permissions on resolv.conf so it is editable
	telnet.write('sudo chmod 666 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#Append new DNS servers to resolv.conf
	telnet.write(nameserverOneCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	telnet.write(nameserverTwoCommand + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	#Set permissions back
	telnet.write('sudo chmod 644 /etc/resolv.conf' + '\n')
	response = telnet.read_until('cisco@virl-sim-server:~$')
	lineNumber = 3
	#For each IOSv device on the topology
	for key, val in ipDictionary.iteritems():
		#Add a name entry to hosts so it user can connect via hostname
		telnet.write('sudo sed -i "' + str(lineNumber) + 'i ' + val + ' ' + key + '" /etc/hosts' + '\n')
		response = telnet.read_until('cisco@virl-sim-server:~$')
		lineNumber +=1
	telnet.close()
	print 'virl-sim-server interfaces updated. Server available @ ' + SNATAddress

if __name__ == "__main__":
	#IP Address of the VIRL server 
	virlHost = "158.125.102.75"
	#Credentials for the account
	username = "rob"
	password = "rrr"
	#URL to create a simulation
	url = "http://virl.lboro.ac.uk:19399/simengine/rest/launch"
	#URL that provides information about a simulation
	hostsURL = "http://virl.lboro.ac.uk:19399/roster/rest/"
	#Saves the virl file to a variable
	topology = open('topology.virl', 'r')
	#Specifies type of data
	headers = {'content-type': 'text/xml'}
	#Sprecifies a string to prepend the ID of a simulation
	payload = {'file': 'manual@launch_topo'}

	#Makes a call to the VIRL host, creates a simulation and stores the returned data to a variable
	try:
		result = requests.post(url, auth=(username,password), params=payload, data=topology, headers=headers, timeout=10)
		#The text of result is an ID for the simulation
		simulationName = result.text
		print 'Simulation ID is: ' + simulationName
		print 'Waiting for simulation launch'
		time.sleep(45) #Required as it takes time for ip addresses to be generated
		print 'Gathering simulation information'
		#Makes a call for information about current hosts
		try:
			hostInformation = requests.get(hostsURL, auth=(username, password), timeout=5)
		except:
			print 'VIRL server did not respond within timeout'
		#Returned data is JSON, it is parsed by the JSON library
		hostJSON = json.loads(hostInformation.text)
		ipDictionary = {}
		serverManIP = ''
		serverExtIP = ''
		SNATAddress = ''
		consolePort = ''
		deviceConsolePort = '' 

		#Deletes user cell of json as no longer needed
		del hostJSON['UUID']

		#Iterates over all nodes available for a user
		for key, val in hostJSON.iteritems():
			#Stores the node information in a variable
			rawDeviceInfo = val
			#If the device is under the current simulation
			if rawDeviceInfo['simID'] == simulationName:
				for devKey, devVal in rawDeviceInfo.iteritems():
					#If an IOS node is seen, get it's name and management IP
					if ((devKey == 'NodeSubtype') and (devVal == 'IOSv')):
						hostname = rawDeviceInfo['NodeName']
						managementIP = rawDeviceInfo['managementIP']
						ipDictionary[str(hostname)] = str(managementIP)
					#If the virl-sim-server is found get information about it
					if ((devKey == 'NodeName') and (devVal == 'virl-sim-server')):
						serverManIP = rawDeviceInfo['managementIP']
						serverExtIP = rawDeviceInfo['internalAddr']
						SNATAddress = rawDeviceInfo['externalAddr']
						consolePort = rawDeviceInfo['PortConsole']
		#Call function to configure virl-sim-server
		setupServer(serverManIP, serverExtIP, virlHost, consolePort, SNATAddress, ipDictionary)
	except:
		print 'VIRL server did not respond within timeout'