#!/bin/bash
echo "Updating capcodes"
./convert/tools/gen_db_capcodes.py
echo "Updating plaatsnamen"
./convert/tools/gen_db_plaatsnamen.py
echo "Updating plaatsnaamafkortingen"
./convert/tools/gen_db_pltsnmn.py
echo "Updating match regions (skipped, filter not implemented yet)"
#./convert/tools/gen_match_regions.py
echo "Updating match disciplines (skipped, filter not implemented yet)"
#./convert/tools/gen_match_disciplines.py
echo "Restart HAp2000 service"
sudo systemctl restart rtlsdrp2000.service
