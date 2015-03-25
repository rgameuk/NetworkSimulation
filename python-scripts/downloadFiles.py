import pysftp

with pysftp.Connection('178.62.24.178', username='sftp', private_key='/home/rob/.ssh/id_rsa') as sftp:
	sftp.get_d('json-files', '/var/www/html')
	sftp.get_d('virl-files', '/var/www/html')
print 'Script has been run'