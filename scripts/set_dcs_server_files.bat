@echo off

xcopy C:\Users\mcdel\Dropbox\Missions "C:\Users\mcdel\Saved Games\DCS.openbeta_server\Missions" /y
xcopy C:\Users\mcdel\Dropbox\MissionScripting  "C:\Users\mcdel\Saved Games\DCS.openbeta_server\MissionScripting" /y

REM Ensure santatize lua is disabled for mission persistence
copy C:\Users\mcdel\Dropbox\MissionScripting\MissionScripting.lua  "C:\Users\Program Files\Eagle Dynamics\DCS.openbeta_server\Scripts\MissionScripting.lua"

copy C:\Users\mcdel\Dropbox\MissionScripting\slmod_config.lua  "C:\Users\Program Files\Eagle Dynamics\DCS.openbeta_server\Slmod\config.lua"
