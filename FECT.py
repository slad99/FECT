# -*- encoding: utf-8 -*-
#
#  FECT/FECT.py
#  
#  Author: Jean-Philippe Teissier ( @Jipe_ )
#    
#  This work is licensed under the GNU General Public License
#
#  Dependencies: pywin32
#

import subprocess
import re
import zipfile
import os
import sys
import argparse
import datetime
import pythoncom
import pywintypes
import win32api
from win32com.shell import shell

__version__ = '0.1'

# This is the autorunsc.exe (6677b6017e5d470cf99ef60d1802bccc) v11.70 from http://technet.microsoft.com/en-us/sysinternals/bb963902.aspx

def Main():
	''' main '''
	parser = argparse.ArgumentParser(description='Use Microsoft autorunsc to identify binaries launched at windows startup and zip all the binaries to an archive')
	parser.add_argument('-a', '--autorunsc_options', help='Wrapped options passed to autorunsc. E.g.: pyAutoruns.py -a \"-b -s -c -f\" Double quotes are Mandatory. -c is Mandatory as well.')
	args = parser.parse_args()

	print '\n[*] FECT v' + __version__ + ' by @Jipe_\n'

	if shell.IsUserAnAdmin():

		print '[*] That\'s fine, I\'m running with Administrator privileges'

		autorunsc_options = '-a -c -m -f'	#All entries with the respective hashes, except the one from Microsoft, with a CSV output 

		if args.autorunsc_options:
			autorunsc_options = args.autorunsc_options

		path_regex = re.compile('\"([a-z]:[\w\\\s-]+?\.\w{3})[\s\"]{1}', flags=re.IGNORECASE)			#match normal paths
		path_with_var_regex = re.compile('\"(%\w+%[\w\\\s-]+?\.\w{3})[\s\"]{1}', flags=re.IGNORECASE)	#match paths using an %environementvariables%

		systemroot_regex = re.compile('%SystemRoot%', flags=re.IGNORECASE)
		windir_regex = re.compile('%windir%', flags=re.IGNORECASE)
		programfiles_regex = re.compile('%ProgramFiles%', flags=re.IGNORECASE)

		env_var_windir = os.getenv('windir')
		env_var_programfiles = os.getenv('ProgramFiles')
		env_var_systemroot = os.getenv('SystemRoot')

		try:
			with open('tmp_autorunsc.exe', 'wb') as f:
				print '[*] Writing tmp_autorunsc.exe to the drive'
				f.write(autorunsc_hex_encoded.decode('hex'))
		except:
			print '[!] Error writing tmp_autorunsc.exe binary to the drive'

		try:
			autorunsc_csv_results = subprocess.check_output('tmp_autorunsc.exe ' + autorunsc_options + ' -\"accepteula\"', stderr=subprocess.STDOUT, universal_newlines=True)
			autorunsc_csv_results = autorunsc_csv_results.decode('utf-16').encode('utf-8')
			
			file_paths = path_regex.findall(autorunsc_csv_results)
			file_paths_with_var = path_with_var_regex.findall(autorunsc_csv_results)
			file_paths_with_var_replaced = []

			for file_path_with_var in file_paths_with_var:
				match = systemroot_regex.search(file_path_with_var)
				if match:
					file_paths_with_var_replaced.append(re.sub(systemroot_regex, env_var_systemroot, file_path_with_var))
				match = programfiles_regex.search(file_path_with_var)
				if match:
					file_paths_with_var_replaced.append(re.sub(programfiles_regex, env_var_programfiles, file_path_with_var))
				match = windir_regex.search(file_path_with_var)
				if match:
					file_paths_with_var_replaced.append(re.sub(windir_regex, env_var_systemroot, file_path_with_var))
			
			file_paths_with_var_replaced
			file_paths = file_paths + file_paths_with_var_replaced
			nb_paths = str(len(file_paths))

			print '[*] ' + nb_paths + ' binaries paths found'
			try:
				with open('autorunsc_csv_results.csv', 'w+') as acr:
					acr.write(autorunsc_csv_results)

				debug_hostname = os.getenv('COMPUTERNAME')
				if debug_hostname is None: debug_hostname = 'UnspecifiedHostname'
				
				debug_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
				
				debug_filename = 'FECT' + debug_hostname + '_' + debug_date + '.txt'
				print '[*] ' + debug_filename

				with open(debug_filename, 'w+') as host_info:
					host_info.write(debug_filename)

			except IOError as e:
				print '[!] Error: ' + e.strerror
			except:
				print '[!] Unexpected error:', sys.exc_info()[0]

		except subprocess.CalledProcessError as e:
			print '[!] Error executing autorunsc: ' + str(e.output)

		try:
			with zipfile.ZipFile('FECT_found_binaries_' + debug_hostname + '_' + debug_date + '.zip', 'w') as zf:
				nb_files = 1
				nb_errors = 0
				zf.write('autorunsc_csv_results.csv')
				zf.write(debug_filename)
				for file_path in file_paths:
					print '[+] [' + str(nb_files) + '/' + nb_paths + '] Adding ' + file_path
					try:
						zf.write(file_path)
						nb_files += 1
					except (IOError, WindowsError) as e:
						print '[!] Error adding ' + file_path + ': ' + e.strerror
						nb_errors += 1
						pass
					except:
						print '[!] Error adding', sys.exc_info()[0]
						nb_errors += 1
						pass
				print '\n[+] ' + str(nb_files) + ' files added to the zip archive with ' + str(nb_errors) + ' errors'
		except IOError as e:
			print '[!] Error({0}): {1}'.format(e.errno, e.strerror)
		except:
			print '[!] Unexpected error:', sys.exc_info()[0]
	
		try:
			os.remove('tmp_autorunsc.exe')			
			os.remove('autorunsc_csv_results.csv')
			os.remove(debug_filename)
		except:
			print '[!] Error removing temporary files. You have to do the cleaning by yourself.'

	else:
		print '[!] Error, the script has to be run with Administrator privileges (Right click on me -> Run as an Administrator)'

if __name__ == '__main__':
	Main()