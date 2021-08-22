#!/usr/bin/env python3
import time
import os
import csv
import sys

# Change dir to working directory
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
os.chdir('../..')

if (not os.path.exists('convert')):
   print('Cannot find working directory of p2000')
   sys.exit(0)

# Create timestamp
timestamp = time.strftime("%Y%m%d-%H%M%S")

# Backup current capcode file with timestamp added
os.rename(r'match_regions.txt',r'convert' + timestamp + '-match_regions.txt')

# Read all region values and generate a unique list in match_regios.txt file
with open('db_capcodes.txt', 'r') as infile, open('match_regions.txt', 'w') as outfile:

    fieldnames = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']
    listRegions = []

    reader = csv.DictReader(infile, delimiter=',', fieldnames=fieldnames)
    for row in reader:
       if row['region'] in listRegions or row['region'] == 'region':
           continue
       else:
           print(row['region'])
           outfile.write(row['region']+'\n')
           listRegions.append(row['region'])

outfile.close()
infile.close()
