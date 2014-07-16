from fabric.api import local

def deploy_live():
    print 'deploy'
    local("uname -a")