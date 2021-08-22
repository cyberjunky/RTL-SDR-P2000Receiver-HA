#!/usr/bin/env python3
import requests
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

# Backup current csv-files with timestamp added
try:
   os.rename(r'convert/cap2csv.php',r'convert/' + timestamp + '-cap2csv.php')
   os.rename(r'convert/bommel_capfiles.csv',r'convert/' + timestamp + '-bommel_capfiles.csv')
   os.rename(r'convert/zulu_capfiles.csv',r'convert/' + timestamp + '-zulu_capfiles.csv')
except:
   pass

# Backup current capcode file with timestamp added
try:
   os.rename(r'db_capcodes.txt',r'convert/' + timestamp + '-db_capcodes.txt')
   os.rename(r'convert/bommel_db_capcodes.txt',r'convert/' + timestamp + '-bommel_db_capcodes.txt')
   os.rename(r'convert/zulu_db_capcodes.txt',r'convert/' + timestamp + '-zulu_db_capcodes.txt')
except:
   pass

# Download latest capcodes from Bommel and Zulu00
print('Get bommel capcodes')
rbo = requests.get('http://p2000.bommel.net/cap2csv.php')
print('Write Bommel capcodes to csv file')
open('convert/bommel_capfiles.csv', 'wb').write(rbo.content)
regionumber = 1
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r01 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=150024335')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r02 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=198860755')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r03 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1300538908') 
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r04 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1578088275') 
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r05 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=462716474') 
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r06 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=352644046')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r07 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=749319406')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r08 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1306650475')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r09 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=194825636')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r10 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=649049634')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r11 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=532936397')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r12 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1778302543')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r13 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=495911126')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r14 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=396051724')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r15 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=371849753')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r16 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1174748477')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r17 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=740604061')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r18 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=152331628')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r19 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=218400779')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r20 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=937575053')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r21 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=671328448')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r22 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=945625928')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r23 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=790598252')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r24 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1352853100')
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r25 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=1499593657') 
print(f'Get Zulu capcodes Regio {regionumber}')
regionumber = regionumber + 1
r26 = requests.get('https://docs.google.com/spreadsheets/d/1wzH_REDdXb_ra3qek4eU1pbKBaALLjL65uYfmR9cay4/export?format=csv&gid=586908396')

regionumber = 1
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'wb').write(r01.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r02.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r03.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r04.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r05.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r06.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r07.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r08.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r09.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r10.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r11.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r12.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r13.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r14.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r15.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r16.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r17.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r18.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r19.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r20.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r21.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r22.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r23.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r24.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r25.content)
open('convert/zulu00_capfiles.csv', 'a').write("\n")
print(f'Write Zulu capcodes Regio {regionumber} to csv file')
regionumber = regionumber + 1
open('convert/zulu00_capfiles.csv', 'ab').write(r26.content)

# remove multiple headers from Zulu csv file
print('Remove multiple headers from Zulu csv file')
lines = list()
headertext= 'regio'
with open('convert/zulu00_capfiles.csv', 'r') as readFile:
   reader = csv.reader(readFile)
   for row in reader:
      lines.append(row)
      for field in row:
            if headertext in field:
               lines.remove(row)
with open('convert/zulu00_capfiles.csv', 'w') as writeFile:
   writer = csv.writer(writeFile)
   writer.writerows(lines)

# Convert downloaded Zulu capcodes to formatted db_capcodes.txt file
print('Convert Zulu csv to structured txt file')
with open('convert/zulu00_capfiles.csv', 'r') as infile, open('convert/zulu_db_capcodes.txt', 'w') as outfile:
    fieldnamesin = ['region', 'location', 'discipline', 'capcode', 'description', 'remark']
    fieldnamesout = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']
    writer = csv.DictWriter(outfile, fieldnames=fieldnamesout, delimiter=',', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
    writer.writeheader()
    reader = csv.DictReader(infile, delimiter=',', fieldnames=fieldnamesin)
    for row in reader:
       writer.writerow({'capcode': row['capcode'].zfill(9), 'discipline': row['discipline'].replace("BRW","Brandweer").replace("POL","Politie").replace("AMBU","Ambulance").replace("BRUG","Gemeente").replace("KNRM","Reddingsbrigade"), 'region': row['region'].replace("01","Groningen").replace("02","Friesland").replace("03","Drenthe").replace("04","IJsseland").replace("05","Twente").replace("06","Noord-Oost Gelderland").replace("07","Gelderland Midden").replace("08","Gelderland Zuid").replace("09","Utrecht").replace("10","Noord-Holland Noord").replace("11","Zaanstreek Waterland").replace("12","Kennemerland").replace("13","Amsterdam-Amstelland").replace("14","Gooi en Vechtstreek").replace("15","Haaglanden").replace("16","Hollands-Midden").replace("17","Rotterdam-Rijnmond").replace("18","Zuid-Holland Zuid").replace("19","Zeeland").replace("20","Midden-en West Brabant").replace("21","Brabant-Noord").replace("22","Brabant-Zuidoost").replace("23","Limburg-Noord").replace("24","Limburg-Zuid").replace("25","Flevoland"), 'location': row['location'], 'description': row['description'].strip(), 'remark': row['remark'].strip()})

infile.close()
outfile.close()

# Convert downloaded Bommel capcodes to formatted db_capcodes.txt file
print('Convert Bommel csv to structured txt file')
with open('convert/bommel_capfiles.csv', 'r') as infile, open('convert/bommel_db_capcodes.txt', 'w') as outfile:

    fieldnames = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
    writer.writeheader()

    reader = csv.DictReader(infile, delimiter=';', fieldnames=fieldnames)
    for row in reader:
       writer.writerow({'capcode': row['capcode'].zfill(9), 'discipline': row['discipline'], 'region': row['region'], 'location': row['location'], 'description': row['description'].strip(), 'remark': row['remark'].strip()})

infile.close()
outfile.close()



# merge bommel and zulu00 bommel_capfiles
print('Merge Zulu en Bommel capcodes and write to capcodes_db.txt')

fields = ['capcode', 'discipline', 'region', 'location', 'description', 'remark']

with open('convert/bommel_db_capcodes.txt', 'r') as readFile_bommel:
    with open('db_capcodes.txt', 'w') as results:
            with open('convert/zulu_db_capcodes.txt', 'r') as readFile_zulu:
                master = csv.DictReader(readFile_zulu, fieldnames=fields)
                update = csv.DictReader(readFile_bommel, fieldnames=fields)
                writer = csv.DictWriter(results, fieldnames=fields)

                # Saves and skips header to output file
                writer.writerow(next(master))
                next(update)

                seen = set()
                for row in update:
                    writer.writerow(row)
                    seen.add(row['capcode'])

                for row in master:
                    if row['capcode'] not in seen:
                        writer.writerow(row)

readFile_zulu.close()
readFile_bommel.close()
results.close()
