@echo off
start C:\cygwin64\bin\bash --login -c "cd C:/Users/mcdel/dcs-wb-magic/; python run_servers.py"

CD "C:\Program Files (x86)\DCS-SimpleRadio-Standalone\"

tasklist /nh /fi "imagename eq SR-ClientRadio.exe" | find /i "SR-ClientRadio.exe" > nul || (start "" "SR-ClientRadio.exe")

tasklist /nh /fi "imagename eq VoiceAttack.exe" | find /i "VoiceAttack.exe" > nul || (start "" "C:\Program Files (x86)\Steam\steamapps\common\VoiceAttack\VoiceAttack.exe")

tasklist /nh /fi "imagename eq joystick_gremlin.exe" | find /i "joystick_gremlin.exe" > nul || (start "" "C:\Users\mcdel\Desktop\Joystick Gremlin.lnk")
