import os
import subprocess

if __name__ == "__main__":
	username = 'rancid'
	password = 'rancid'
	routerList = {'R1':'172.30.0.1','R2':'172.30.0.2', 'R3':'172.30.0.3'}
	hostsFile = '/etc/hosts'

	for val in routerList:
		print val

	#with open('/etc/rancid/rancid.conf','a') as f:
	#	f.write('LIST_OF_GROUPS="Discovered"')
	#	f.close()

	with open('/etc/hosts','a') as f:
		for key, value in routerList.iteritems():
			entry = value + "\t" + key + "\n"
			print entry
			f.writelines(entry)
	f.close()

	os.setuid(104)
	subprocess.check_output("/var/lib/rancid/bin/rancid-cvs")

	with open('/var/lib/rancid/Discovered/router.db','a') as f:
		for key, value in routerList.iteritems():
			entry = key + ":cisco:up" + "\n"
			f.writelines(entry)
	f.close()

	with open('/var/lib/rancid/.cloginrc','a') as f:
		for key, value in routerList.iteritems():
			entry = "#" + key.lower() + "\n"
			f.writelines(entry)
			entry = "add method " + key.lower() + " {ssh}" + "\n"
			f.writelines(entry)
			entry = "add cyphertype " + key.lower() +  " {des}" + "\n"
			f.writelines(entry)
			entry = "add user " + key.lower() + " {rancid}" + "\n"
			f.writelines(entry)
			entry = "add password " + key.lower() + " {rancid} {rancid}" + "\n" + "\n"
			f.writelines(entry)

	subprocess.check_output("/var/lib/rancid/bin/rancid-run")