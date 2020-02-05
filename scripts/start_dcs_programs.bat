@echo off

copy C:\Users\mcdel\dcs-wp-magic\Plugin\WPManager.lua  "C:\Users\mcdel\Saved Games\DCS\Scripts\Hooks\WPManager.lua"
copy C:\Users\mcdel\dcs-wp-magic\Plugin\WPManager.dlg  "C:\Users\mcdel\Saved Games\DCS\Scripts\WPManager\WPManager.dlg"

copy C:\Users\mcdel\dcs-wp-magic\Plugin\mist.lua  "C:\Users\mcdel\Saved Games\DCS\Scripts\mist.lua"
copy C:\Users\mcdel\dcs-wp-magic\Plugin\CTLD.lua  "C:\Users\mcdel\Saved Games\DCS\Scripts\CTLD.lua"

CD "C:\Program Files (x86)\H2ik\Joystick Gremlin\"
tasklist /nh /fi "imagename eq joystick_gremlin.exe" | find /i "joystick_gremlin.exe" > nul || (start "" "C:\Program Files (x86)\H2ik\Joystick Gremlin\joystick_gremlin.exe")

CD "C:\Users\mcdel\dcs-wp-magic\"
tasklist /nh /fi "imagename eq dcs_wp_manager.exe" | find /i "dcs_wp_manager.exe" > nul || (start "" "C:\Users\mcdel\dcs-wp-magic\dist\dcs_wp_manager\dcs_wp_manager.exe")

(tasklist /nh /fi "imagename eq SimShaker for Aviators beta.exe") | find /i "SimShaker" > nul || (start "" "C:\Users\mcdel\Desktop\SimShaker for Aviators beta.appref-ms")

CD "C:\Users\mcdel\"
(tasklist /nh /fi "imagename eq DCS.exe") | find /i "DCS.exe" > nul || (start "" "C:\Program Files (x86)\Steam\steamapps\common\DCSWorld\bin\DCS.exe")

CD "C:\Program Files (x86)\DCS-SimpleRadio-Standalone\"
tasklist /nh /fi "imagename eq SR-ClientRadio.exe" | find /i "SR-ClientRadio.exe" > nul || (start "" "SR-ClientRadio.exe")

tasklist /nh /fi "imagename eq VoiceAttack.exe" | find /i "VoiceAttack.exe" > nul || (start "" "C:\Program Files (x86)\Steam\steamapps\common\VoiceAttack\VoiceAttack.exe")
