from fabric.api import run

def deploy_live():
    print 'deploy'
    run("uname -a")