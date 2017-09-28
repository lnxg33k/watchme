## WatchMe (WM)
![Start_all_watchers](https://user-images.githubusercontent.com/1170490/30958672-80d8bf36-a446-11e7-9f25-980669eb8a3b.png)
![Show_all_configs](https://user-images.githubusercontent.com/1170490/30958705-a15057ba-a446-11e7-919c-a4f4f7a3b224.png)
![Show_all_hits](https://user-images.githubusercontent.com/1170490/30958748-ba0bed8c-a446-11e7-8e5b-e8b557c2e6f8.png)
![Show_single_hit](https://user-images.githubusercontent.com/1170490/30958773-d168c5e0-a446-11e7-8a55-12400d734082.png)

## What is WatchMe?
WatchMe is a high level file system watcher built in top of watchdog python module for watching file changes on a specific path and give alerts based on an event.

## Why was it built?
If you are working for an enterprise and you have lots of web-servers "doesn't matter if they are IIS, apache or whatever", you can just mount them remotely and make WatchMe notify incase some files were added, modified, moved or even deleted.

## Installation
Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install python-pip cifs-utils rabbitmq-server
sudo pip install virtualenv
```
Setup RabbitMQ virtual server:
```bash
sudo rabbitmqctl add_vhost watcher
sudo rabbitmqctl add_user watcher "Raya_123!"
sudo rabbitmqctl set_permissions -p watcher watcher ".*" ".*" ".*"
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
## Wrapping up
**_Please note, for development deployments only_**

Configure the Django application:
```bash
python manage.py createsuperuser --username admin --email administrator@localhost
python manage.py runserver
```
Setup a debug SMTP server for alerting:
```bash
python -m smtpd -n -c DebuggingServer localhost:1025
```
Create the configs for the mount points:

WatchMe provides a CLI along with the web-app, so to create a mountpoint and start watching it, you can do it in two different ways:
  1. http://localhost:8000/APIs/watcherconfig/ and create the config
  2. From the cli:
      - ` python manage.py config -s "TestServer#1" -sharepath ~/Desktop/mountpoint/ -patterns "*.aspx" --tags "iis" --comment "Server IP: 192.168.1.23"`

Watch the created config:
  - `python manage.py watcher -c start -s TestServer#1`

# Django custom management commands
For more help, you can run
```bash
python manage.py watcher -h
python manage.py config -h
```

## TODO
- [x] Add an alerting functionality.
- [x] Check if the file was seen before.
- [x] Save the content of the file in the DB.
- [x] Use Yara rules on the content of the file.
- [ ] The task should be per event along with the Q.
- [ ] Yara rules should be per tag or the server.
