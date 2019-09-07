@echo off
CD "C:\Program Files (x86)\DCS-SimpleRadio-Standalone\"
start "" "SR-ClientRadio.exe"
start "" "C:\Program Files (x86)\Steam\steamapps\common\VoiceAttack\VoiceAttack.exe"

CD "C:\Users\mcdel\dcs-wb-magic"
start "C:\Users\mcdel\Anaconda3\python.exe" "C:/Users/mcdel/dcs-wb-magic/socket_client.py"
call activate base
"C:\Users\mcdel\Anaconda3\python.exe" "C:/Users/mcdel/dcs-wb-magic/server.py"
