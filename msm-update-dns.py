#! /usr/bin/python

import ovh,sys
client=ovh.Client()
recid=client.get('/domain/zone/isil.paris/record?subDomain=_minecraft._tcp')[0]
if(len(sys.argv)>=2):
	client.put('/domain/zone/isil.paris/record/%d'%recid, target="0 0 25565 %s" % sys.argv[1])
	print "Updated record %d"%recid
