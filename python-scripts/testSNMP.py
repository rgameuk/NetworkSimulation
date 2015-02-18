import os
print "Hello, World";
f=os.popen("snmpwalk -v 2c -c public 172.30.0.1 1.3.6.1.4.1.9.9.23.1.2.1.1.6")
for i in f.readlines():
	print "line:", i,
