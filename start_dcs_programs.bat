@echo off

CD "C:\Program Files (x86)\DCS-SimpleRadio-Standalone\"
tasklist /nh /fi "imagename eq SR-ClientRadio.exe" | find /i "SR-ClientRadio.exe" > nul || (start "" "SR-ClientRadio.exe")

tasklist /nh /fi "imagename eq VoiceAttack.exe" | find /i "VoiceAttack.exe" > nul || (start "" "C:\Program Files (x86)\Steam\steamapps\common\VoiceAttack\VoiceAttack.exe")

tasklist /nh /fi "imagename eq joystick_gremlin.exe" | find /i "joystick_gremlin.exe" > nul || (start "" "C:\Program Files (x86)\H2ik\Joystick Gremlin\joystick_gremlin.exe")

CD "C:\Users\mcdel\dcs-wp-magic\"
(start "" "C:\Users\mcdel\dcs-wp-magic\dist\dcs_wp_manager\dcs_wp_manager.exe")
