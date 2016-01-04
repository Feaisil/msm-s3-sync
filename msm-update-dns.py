#! /usr/bin/python

def update(dns):
	import ovh,sys
	client=ovh.Client()
	recid=client.get('/domain/zone/isil.paris/record?subDomain=_minecraft._tcp')[0]
	client.put('/domain/zone/isil.paris/record/%d'%recid, target="0 0 25565 %s" % dns)
	print "Updated record %d"%recid

if __name__=="__main__":
	if(len(sys.argv)>=2):
		update(sys.argv[1])

