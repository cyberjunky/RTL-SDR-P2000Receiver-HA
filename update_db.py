#!/bin/bash
echo "update capcodes"
./convert/tools/gen_db_capcodes.py
echo "update plaatsnamen"
./convert/tools/gen_db_plaatsnamen.py
echo "update plaatsnaamafkortingen"
./convert/tools/gen_db_pltsnmn.py
echo "update match regions"
./convert/tools/gen_match_regions.py
echo "update match disciplines"
./convert/tools/gen_match_disciplines.py
echo "Restart HAp2000 service"
systemctl restart HA-p2000.service
