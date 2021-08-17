#!/usr/bin/env python3
import requests
import time
import os
import csv

# Change dir to working directory
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
os.chdir('../..')

if (not os.path.exists('tools')):
   print('Cannot find working directory of p2000')
   sys.exit(0)

# Create timestamp
timestamp = time.strftime("%Y%m%d-%H%M%S")

# Rename current afkortingen_plaatsnamen.csv file with timestamp added
try:
   os.rename(r'convert/afkortingen_plaatsnamen.csv',r'convert/' + timestamp + '-afkortingen_plaatsnamen.csv')
except:
   pass

# Download latest plaatsnamen as Afkortingen_Plaatsnamen.csv file
r = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1235300646')
open('convert/afkortingen_plaatsnamen.csv', 'wb').write(r.content)

# Backup current db_plaatsnamen.txt file with timestamp added
os.rename(r'db_plaatsnamen.txt',r'convert/' + timestamp + '-db_plaatsnamen.txt')

# Convert downloaded plaatsnamen.csv to formatted db_plaatsnamen.txt file
with open('convert/afkortingen_plaatsnamen.csv', 'r') as infile, open('db_plaatsnamen.txt', 'w') as outfile:

    fieldnames = ['plaatsnaam']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
    writer.writeheader()

    fieldnames = ['Plaatsnaam']
    reader = csv.DictReader(infile, delimiter=',', fieldnames=fieldnames)
    for row in reader:
       if row['Plaatsnaam'] == 'Plaatsnaam':
           continue
       else:
           print(row['Plaatsnaam'])
           writer.writerow({'plaatsnaam': row['Plaatsnaam']})

infile.close()
outfile.close()
