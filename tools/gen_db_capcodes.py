#!/usr/bin/env python3
import requests
import time
import os
import csv

# Change dir to working directory
os.chdir('..')

if (not os.path.exists('tools')):
   print('Cannot find working directory of p2000')
   sys.exit(0)

# Create timestamp
timestamp = time.strftime("%Y%m%d-%H%M%S")

# Backup current cap2csv.php file with timestamp added
try:
   os.rename(r'convert/cap2csv.php',r'convert/' + timestamp + '-cap2csv.php')
except:
   pass

# Download latest capcodes as cap2csv.php file
r = requests.get('http://p2000.bommel.net/cap2csv.php')
open('convert/cap2csv.php', 'wb').write(r.content)

# Backup current capcode file with timestamp added
os.rename(r'db_capcodes.txt',r'convert/' + timestamp + '-db_capcodes.txt')

# Convert downloaded capcodes to formatted db_capcodes.txt file
with open('convert/cap2csv.php', 'r') as infile, open('db_capcodes.txt', 'w') as outfile:

    fieldnames = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
    writer.writeheader()

    reader = csv.DictReader(infile, delimiter=';', fieldnames=fieldnames)
    for row in reader:
       writer.writerow({'capcode': row['capcode'].zfill(9), 'discipline': row['discipline'], 'region': row['region'], 'location': row['location'], 'description': row['description'], 'remark': row['remark']})

infile.close()
outfile.close()
