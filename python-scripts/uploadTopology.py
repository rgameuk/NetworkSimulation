import os, requests, sys

virlHost = "178.62.24.178"
username = "rob"
password = "rrr"
url = "http://virl.lboro.ac.uk:19399/simengine/rest/launch"
topology = open('virlservertest.virl', 'r')
headers = {'content-type': 'text/xml'}
payload = {'file': 'manual@launch_topo'}

result = requests.post(url, auth=(username,password), params=payload, data=topology, headers=headers)
print result.text
