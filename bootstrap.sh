cd /vagrant

sudo apt-get install -y build-essential software-properties-common python-software-properties

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list

sudo apt-get update

sudo apt-get -y install mongodb-org

sudo apt-get -y install libxml2-dev libxslt1-dev python-dev
sudo wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python
sudo apt-get -y install python-pip
sudo apt-get -y install rubygems1.9.1
wget -qO- https://toolbelt.heroku.com/install-ubuntu.sh | sh
sudo pip install tornado
sudo pip install pymongo
sudo pip install requests requests_oauthlib
sudo pip install apscheduler
sudo pip install Jinja2
sudo pip install google-api-python-client