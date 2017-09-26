## WatchMe (WM)
![WM](https://cloud.githubusercontent.com/assets/1170490/18811595/a4537b0a-82bd-11e6-9870-8228d684053b.png)

## What is WatchMe?
WatchMe is a high level file system watcher built in top of watchdog python module for watching file changes on a specific path and give alerts based on an event.

## Why was it built?
If you are working for an enterprise and you have lots of web-servers "doesn't matter if they are IIS, apache or whatever", you can just mount them remotely and make WatchMe notify incase some files were added, modified, moved or even deleted.

## Installation
**Install system dependencies**:
```bash
sudo apt-get update
sudo apt-get install python-pip
sudo pip install virtualenv
```
Clone the GitHub repo:
```bash
git clone https://github.com/lnxg33k/watchme.git
```
Create a Python virtual environment and activate it:
```bash
cd watchme
virtualenv virt
source virt/bin/activate
```
Install Python dependencies:
```bash
pip install -r requirements.txt
```

## TODO
- [x] Add an alerting functionality.
- [x] Check if the file was seen before.
- [x] Save the content of the file in the DB.
- [x] Use Yara rules on the content of the file.
