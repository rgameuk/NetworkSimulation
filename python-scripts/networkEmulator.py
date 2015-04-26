import os

def main():
	validInput = False
	while validInput == False:
		print 'Would you like to discover a local network or use local files?'
		netChoice = input('(1 - local network , 2 - local files)\n')
		if netChoice == 1:
			validInput = True
			validNetChoice = False
			while validNetChoice == False:
				print 'Do you want to specify network boundaries?'
				specifyChoice = input('(1 - Discover all , 2 - Specify Network)\n')
				if specifyChoice == 1:
					validNetChoice = True
					try:
						os.system("python networkDiscovery.py")
						os.system("python rancidSetup.py")
						os.system("python configFormatter.py")
						os.system("python virlCreation.py")
					except:
						print 'Network extraction failed'
				elif specifyChoice == 2:
					validNetChoice = True
					try:
						os.system("python networkDiscovery.py --specify")
						os.system("python rancidSetup.py")
						os.system("python configFormatter.py")
						os.system("python virlCreation.py")
					except:
						print 'Network extraction failed'
				else:
					print 'Invalid entry, please try again'
		elif netChoice == 2:
			validInput = True
			try:
				os.system("python networkLoad.py")
				os.system("python configFormatter.py --noCopy")
				os.system("python virlCreation.py")
			except:
				print 'Network extraction failed'
		else:
			print 'Invalid entry, please try again'

if __name__ == "__main__":
	main()
