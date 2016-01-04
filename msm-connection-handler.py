#!/usr/bin/python
started = False
server_id = None
server_region = None
import subprocess, time, msmupdatedns
import boto3 as aws

msm = "/usr/local/bin/msm"
ami='ami-accff2b1'
def broadcast(message):
	subprocess.check_call([msm, "manager", "say",message])
def check_server_status():
	ec2=aws.resource('ec2')
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
	ec2=aws.resource('ec2')
	instance=ec2.create_instances( ImageId=ami, MinCount=1, MaxCount=1, KeyName='minecraftsyd', SecurityGroups=['mc'], InstanceType='t2.micro', InstanceInitiatedShutdownBehavior='terminate')[0]
	server_id = instance.id
	server_region=region
	instance.wait_until_running()	
	instance=ec2.Instance(id=instance.id)
	msmupdatedns.update(instance.public_dns_name)
	started=True
	broadcast("The server is started, and available in up to 60 seconds")

if __name__=="__main__":
	while True:
		try:
			lsof = subprocess.check_output(["lsof","-iTCP:25565","-sTCP:ESTABLISHED"])
		except:
			time.sleep(5)
			continue
		ip =  lsof.split('->')[1].split(':')[0]
		broadcast("Welcome to this loby server")
		if started:
			check_server_status()
		if not started: #Note: check_server_status might update this
			start_remote_Server()
		time.sleep(60)
		broadcast("The server should be available now, the loby will close")
		subprocess.check_call([msm,"manager","restart"])
		time.sleep(60)

