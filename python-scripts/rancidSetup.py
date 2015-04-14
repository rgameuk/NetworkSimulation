import os
import subprocess
import pwd
import pickle
import shutil
import getpass

if __name__ == "__main__":
	#Username and password refer to the password used on the Cisco device
	ciscoUsername = 'rancid'
	password = 'rancid'
	enablePassword = 'rancid'
	#routerList was saved to file in networkDiscovery and maps router hostnames to ip addresses
	routerList = pickle.load(open("routerDictionary.p", "rb"))
	print routerList
	#location of the running script so files can be restored if lost
	scriptLocation = '/home/rob/NetworkSimulation/python-scripts'

	#Checks if the Discovered repo already exists - if it does it is removed and rancid is restored to 'default'
	if os.path.isdir('/var/lib/rancid/Discovered'):
		shutil.copyfile(scriptLocation + '/hosts', '/etc/hosts')
		shutil.copyfile(scriptLocation + '/rancid.conf', '/etc/rancid/rancid.conf')
		shutil.rmtree('/var/lib/rancid/Discovered/')
		open('/var/lib/rancid/.cloginrc', 'w').close()

	#Adds a group to rancid for the discovered routers
	if 'LIST_OF_GROUPS="Discovered"' not in open('/etc/rancid/rancid.conf').read():
		with open('/etc/rancid/rancid.conf','a') as f:
			f.write('LIST_OF_GROUPS="Discovered"')
			f.close()

	#Adds entries to hosts for routers so rancid can contact them by hostname
	with open('/etc/hosts','a') as f:
		for key, value in routerList.iteritems():
			entry = value + "\t" + key + "\n"
			print entry
			f.writelines(entry)
	f.close()

	#Rancid should be run as rancid user, so script requests Rancids UID
	rancidUID = pwd.getpwnam('rancid').pw_uid
	print rancidUID
	if os.getuid() == 0:
		os.setuid(rancidUID)
	else:
		print 'Script must be run as root'
	
	#sets the running user to rancid
	username = getpass.getuser()

	#Script defined in rancid - creates repositories for each group defined in rancid.conf
	subprocess.check_output("/var/lib/rancid/bin/rancid-cvs")

	#Adds a router entry for each router that was discovered
	with open('/var/lib/rancid/Discovered/router.db','a') as f:
		for key, value in routerList.iteritems():
			entry = key + ":cisco:up" + "\n"
			f.writelines(entry)
	f.close()

	#Defines the router entries in .cloginrc - uses information defined earlier in the script
	with open('/var/lib/rancid/.cloginrc','a') as f:
		for key, value in routerList.iteritems():
			entry = "#" + key.lower() + "\n"
			f.writelines(entry)
			entry = "add method " + key.lower() + " {ssh}" + "\n"
			f.writelines(entry)
			entry = "add cyphertype " + key.lower() +  " {3des}" + "\n"
			f.writelines(entry)
			entry = "add user " + key.lower() + " {" + ciscoUsername + "}" + "\n"
			f.writelines(entry)
			entry = "add password " + key.lower() + " {" + password + "} {" + enablePassword + "}" + "\n" + "\n"
			f.writelines(entry)

	print 'Running rancid'
	subprocess.check_output("/var/lib/rancid/bin/rancid-run")
	print 'Configuration extraction complete'
