# dcs-wp-magic

## Overview
This project provides the following:

1) A reliable Tacview client, which consumes a remote stream.  Events consumed are written to a GCP PubSub topic, which is itself consumed by a DataFlow cluster that then writes the records to BigQuery.

2) A Flask application which exposes an endpoint from which a DCS player can request enemy coordinates, and their distance from the current player.

3) A DCS plugin that exposes an in-game window to view target coordinates served form the Flask application. Targets can then be selected, and, using DCS-Bios (F/A-18 only, for now), automatically programmed as pre-planned coordinates for JDAM/JSOW destruction.

4) A `tkinter` app that serves as a utility to start and stop the above pieces.


## Installing
If you want to do is more easily wreck havoc from the JSOW/JDAM equipped cockpit of your F/A-18, start by either cloning this repo, or downloading the most recent version from the releases page.

Next, install DCS-BIOS.  There is a script in `misc` that should mostly work.

Then, either copy or symlink the contents of `Plugin` to  `Saved Games\DCS.openbeta\Scripts\`.

Finally, either rebuild the app (`pyinstaller -F -w -y dcs_wp_manager.spec`), or use what is provided in `dist`.  
When that's done, open the .exe, enter the username of your player, the ip address of the Tacview-enabled server (or 127.0.0.1, if you have Tacview running locally) to which you want to connect, and the relevant port.  Note that the default port and host correspond to GAW.


## Using
In game, the WP-Manager window is toggled, by default, with Ctrl+Shift+x.  This can be updated by changing the keybinding configuration in: `Saved Games\DCS.openbeta\Config\WP-Manager-config.lua`. I recommend binding this shortcut to a HOTAS.
Once the window is activated, clicking the `coords` button will refresh the target list, and your current position.

To select a coordinate:
  1) Set the left DDI to the JDAM/JSOW page on in the stores menu, and select all available munitions.
  2) Set PP mode.
  3) Click the numbers corresponding to your desired target.  Targets are referenced by the WP-Manager window buttons.  The first row of buttons corresponds to the target group number, while the second row refers to the target number inside of a specific group.  For example, the select the second target in the first group, you would select the `1` and `2` in the first and second rows, respectively.
  4) Press `stage`.  This queues a target, but does not start the input process.  You can stage between 1 and 8 targets, but be aware the WP-Manager does not know anything about the number of weapons you have, so make sure you stage only as many targets as you have bombs.
  5) Repeat steps 3 and 4 for any additional targets.
  6) Press `enter`.  This triggers WP-Manager to begin inputting the actual target coordinates using the DDI and UFC.  DO NOT TOUCH THE LEFT DDI, UFC, or radio buttons during this process. If you accidentally press one of these buttons and interrupt the process, press `stop` and start again.

If, after you stage targets, you realize you made a mistake, just press the `clear` button.  This will remove any targets previously selected.

If, after you being entering waypoints, you realize that you made a mistake, press the `stop` button.  This will kill the DCS-Bios process that is inputing the coordinates, and allow you to start again.

## Developing
All merges to the master branch automatically trigger GCP Cloud Build to rebuild the Tacview image, and deploy.

To build GUI App locally, run:
```
pyinstaller -F -w -y dcs_wp_manager.spec
```


To build the Tacview consumer locally, run:
```
./scripts/build_dockerfile.sh
```


To run the Tacview client container:
```
docker run -it tacview_reader:dev --host {server_ip} --port {port}
```
