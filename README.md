# dcs-wp-magic
There are four things here:
1) A reliable tacview client consumer, which publishes events to sqlite.

2) A flask server which exposes endpoints to get enemy coordinates and their distance from the current player.

3) A DCS plugin that exposes an in-game UI allowing for the selection of targets served by the flask app, and then to automatically enter their coordinates for JDAM/JSOW destruction.

4) A `tkinter` app that serves as a utility to start and stop the above pieces.


To build GUI App, run:
```
pyinstaller -F -w -y dcs_wp_manager.spec
```


To build the tacview consumer docker container, ensure you have GCP permissions, have the gcloud cli tool installed, and are logged in to allow docker-push.  Then, run:
```
./scripts/build_dockerfile.sh
```


To run the tacview client container:
```
docker run -it tacview_reader:latest --host {server_ip} --port {port}
```
