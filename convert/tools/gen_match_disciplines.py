#!/usr/bin/env python3
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

# Backup current capcode file with timestamp added
os.rename(r'match_disciplines.txt',r'convert/' + timestamp + '-match_disciplines.txt')

# Read all discipline values and create unique list in match_disciplines.txt
with open('db_capcodes.txt', 'r') as infile, open('match_disciplines.txt', 'w') as outfile:

    fieldnames = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']
    listDisciplines = []

    reader = csv.DictReader(infile, delimiter=',', fieldnames=fieldnames)
    for row in reader:
       if row['discipline'] in listDisciplines or row['discipline'] == 'discipline':
           continue
       else:
           print(row['discipline'])
           outfile.write(row['discipline']+'\n')
           listDisciplines.append(row['discipline'])

outfile.close()
infile.close()
