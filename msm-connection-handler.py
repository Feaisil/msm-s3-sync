#!/usr/bin/python

 
import sys, os, time, atexit, errno
from signal import SIGTERM
 
class Daemon:
        """
        A generic daemon class.
       
        Usage: subclass the Daemon class and override the run() method
        """
        def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
                self.stdin = stdin
                self.stdout = stdout
                self.stderr = stderr
                self.pidfile = pidfile
       
        def daemonize(self):
                """
                do the UNIX double-fork magic, see Stevens' "Advanced
                Programming in the UNIX Environment" for details (ISBN 0201563177)
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
                """
                try:
                        pid = os.fork()
                        if pid > 0:
                                # exit first parent
                                sys.exit(0)
                except OSError, e:
                        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
                        sys.exit(1)
       
                # decouple from parent environment
                os.chdir("/")
                os.setsid()
                os.umask(0)
       
                # do second fork
                try:
                        pid = os.fork()
                        if pid > 0:
                                # exit from second parent
                                sys.exit(0)
                except OSError, e:
                        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
                        sys.exit(1)
       
                # redirect standard file descriptors
                sys.stdout.flush()
                sys.stderr.flush()
		try:
			os.makedirs(os.path.dirname(self.stdout))
		except OSError as exc:
			if exc.errno == errno.EEXIST:
				pass
			else:
				raise
		try:
			os.makedirs(os.path.dirname(self.stderr))
		except OSError as exc:
			if exc.errno == errno.EEXIST:
				pass
			else:
				raise
                si = file(self.stdin, 'r')
               	so = file(self.stdout, 'a+')
                se = file(self.stderr, 'a+')
                os.dup2(si.fileno(), sys.stdin.fileno())
                os.dup2(so.fileno(), sys.stdout.fileno())
                os.dup2(se.fileno(), sys.stderr.fileno())
       
		so.write("Daemon %s started\n" % pid)
		se.write("Daemon %s started\n" % pid)

                # write pidfile
                atexit.register(self.delpid)
                pid = str(os.getpid())
                file(self.pidfile,'w+').write("%s\n" % pid)
       
        def delpid(self):
                os.remove(self.pidfile)
 
        def start(self):
                """
                Start the daemon
                """
                # Check for a pidfile to see if the daemon already runs
                try:
                        pf = file(self.pidfile,'r')
                        pid = int(pf.read().strip())
                        pf.close()
                except IOError:
                        pid = None
       
                if pid:
                        message = "pidfile %s already exist. Daemon already running?\n"
                        sys.stderr.write(message % self.pidfile)
                        sys.exit(1)
               
                # Start the daemon
                self.daemonize()
                self.run()
 
        def stop(self):
                """
                Stop the daemon
                """
                # Get the pid from the pidfile
                try:
                        pf = file(self.pidfile,'r')
                        pid = int(pf.read().strip())
                        pf.close()
                except IOError:
                        pid = None
       
                if not pid:
                        message = "pidfile %s does not exist. Daemon not running?\n"
                        sys.stderr.write(message % self.pidfile)
                        return # not an error in a restart
 
                # Try killing the daemon process       
                try:
                        while 1:
                                os.kill(pid, SIGTERM)
                                time.sleep(0.1)
                except OSError, err:
                        err = str(err)
                        if err.find("No such process") > 0:
                                if os.path.exists(self.pidfile):
                                        os.remove(self.pidfile)
                        else:
                                print str(err)
                                sys.exit(1)
 
        def restart(self):
                """
                Restart the daemon
                """
                self.stop()
                self.start()
 
        def run(self):
                """
                You should override this method when you subclass Daemon. It will be called after the process has been
                daemonized by start() or restart().
                """


started = False
server_id = None
server_region = None
import subprocess, time, msmupdatedns
import boto3 as aws

msm = "/usr/local/bin/msm"
ami='ami-79a2bd15'
def broadcast(message):
	subprocess.check_call([msm, "manager", "say",message])
def check_server_status():
	ec2=aws.resource('ec2', region_name=server_region)
	instance=ec2.Instance(id=server_id)
	if instance.state['Code'] == 16:
		broadcast("The server is already started, please try again soon")
		broadcast("or use this ip: "+instance.public_ip_address+" while the dns cache refreshes.")
		msmupdatedns.update(instance.public_dns_name)
	else:
		broadcast("Server not running anymore, will start a new one")
		started=False
		server_id=None
		server_region=None
	
def start_remote_server(region='eu-central-1'):
	broadcast("The server is starting")
	ec2=aws.resource('ec2', region_name=region)
	instance=ec2.create_instances( ImageId=ami, MinCount=1, MaxCount=1, KeyName='minecraftsyd', SecurityGroups=['mc'], InstanceType='r3.large', InstanceInitiatedShutdownBehavior='terminate')[0]
	server_id = instance.id
	server_region=region
	instance.wait_until_running()	
	instance=ec2.Instance(id=instance.id)
	print "updating ovh to "+instance.public_dns_name
	msmupdatedns.update(instance.public_dns_name+".")
	started=True
	broadcast("The server is started, and available in up to 60 seconds")

import sys, time
 
class MyDaemon(Daemon):
        def run(self):
                while True:
               	    try:
               	           lsof = subprocess.check_output(["lsof","-iTCP:25565","-sTCP:ESTABLISHED"])
               	    except:
               	           time.sleep(5)
               	           continue
               	    ip =  lsof.split('->')[1].split(':')[0]
               	    broadcast("Welcome to this lobby server")
               	    if started:
               	           check_server_status()
               	    if not started: #Note: check_server_status might update this
               	           start_remote_server()
               	    time.sleep(60)
               	    broadcast("The server should be available now, the lobby will close")
               	    subprocess.check_call([msm,"manager","restart"])
               	    time.sleep(60)
 
if __name__ == "__main__":
        daemon = MyDaemon('/tmp/daemon-example.pid', stdout="/var/log/mcdaemon/daemon.log", 
		stderr="/var/log/mcdaemon/daemon.err")
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)

