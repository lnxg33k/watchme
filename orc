sudo apt install cifs-utils python-pip virtualenv rabbitmq-server

virtualenv --no-site-packages venv

pip install -r requirements.txt

sudo rabbitmqctl add_vhost watcher
sudo rabbitmqctl add_user watcher "Raya_123!"
sudo rabbitmqctl set_permissions -p watcher watcher ".*" ".*" ".*"

# make home directories executable/readable/writable only by that user
# chmod 700 /home/lnxg33k/

chmod 700 watchme/
cd watchme
find . -type d -print0 | xargs -0 chmod 700
find . -type f -print0 | xargs -0 chmod 600

# remove all secondary groups
# usermod -G "" username
# chmod go-rwx  LogDir   # 500

chmod 600 /root/.dc_smbcredentials
//100.100.100.3/Logs /home/lnxg33k/DC1-IIS cifs file_mode=0500,dir_mode=0500,uid=lnxg33k,gid=lnxg33k,credentials=/root/.dc_smbcredentials,iocharset=utf8,sec=ntlm  0  0
//100.100.100.3/Logs /home/lnxg33k/DC1-IIS cifs file_mode=0400,dir_mode=0500,uid=lnxg33k,gid=lnxg33k,credentials=/root/.dc_smbcredentials,iocharset=utf8,sec=ntlm  0  0
