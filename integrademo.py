#!/usr/bin/env python3

from socket import *
from struct import *
import time
import sys

## Extra debugging
DEBUG = 0

# Delay between consecutive commands 
DELAY=0.3

host=""
port = 7094

# device types as defined by satel manual
PARTITION="00"
ZONE="01"
OUTPUT="04"


def ihex(byte):
	return str(hex(byte)[2:])

''' If you send a second command too soon, ethm1 replies with BUSY messages
so in this demo I am introducing a short pause before each request
obviously, in real life it should be handled smarter, but hey, it is only a demo
''' 
def wait():
	time.sleep(DELAY)

''' Function to calculte a checksum as per Satel manual
beware - it might have a bug!
'''
def checksum(command):
	crc=0x147A;
	for b in command:
		# rotate (crc 1 bit left)
		crc=((crc << 1)  & 0xFFFF) | (crc & 0x8000)>>15
		crc=crc ^ 0xFFFF
		crc=crc + (crc>>8) +  b;
	return crc;

''' All logic is hidden here - this function will send the requests and extract the result
hence the poor man debugging inside
'''
def sendcommand(command):
	data=bytearray.fromhex(command)
	c=checksum(bytearray.fromhex(command))
	data.append(c>>8)
	data.append(c & 0xFF)
	data.replace(b'\xFE',b'\xFE\xF0')

	data=bytearray.fromhex("FEFE")+data+bytearray.fromhex("FE0D")
		
	if DEBUG: 
		print ("-- Sending data --", file=sys.stderr)
		for c in data: print (">>> %s" % hex(c), file=sys.stderr)
		print ("-- ------------- --", file=sys.stderr)
		print ("Sent %d bytes" % len(data), file=sys.stderr)

	sock = socket(AF_INET,SOCK_STREAM)
	sock.connect((host,port))
	if not sock.send(data): raise Exception ("Error Sending message.")
	resp=sock.recv(100)
	if DEBUG: 
		print ("-- Receving data --", file=sys.stderr)
		for c in resp: print ("<<<0x%X ('%c')" % (c,c), file=sys.stderr)
		print ("-- ------------- --", file=sys.stderr)
	sock.close()

	# check message
	if (resp[0:2]!=b'\xFE\xFE'): 
		raise Exception("Wrong header - got %X%X" % (resp[0], resp[1]))
	if (resp[-2:]!=b'\xFE\x0D'): 
		raise Exception ("Wrong footer - got %X%X" % (resp[-2], resp[-1]))

	output=resp[2:-2].replace(b'\xFE\xF0',b'\xFE')
	if output[0]==0xEF:
		raise Exception("Integra reported an error code %X" % output[1])
	if output[0]!=bytearray.fromhex(command[0:2])[0]: 
		raise Exception("Response to a wrong command - got %X expected %X" % (output[0],bytearray.fromhex(command[0:2])[0]))

	c=checksum(bytearray(output[0:-2]))
	if (256*output[-2:-1][0]+output[-1:][0])!=c: 
		raise Exception ("Wrong checksum - got %d expected %d" % ((256*output[-2:-1][0]+output[-1:][0]),c))
	#return only data
	return output[1:-2]
	
''' I only bothered with few of them, feel free to add all newer models
'''
def hardwareModel(code):
	if code==0:
		return "24"
	if code==1:
		return "32"
	if code==2:
		return "64"
	if code==3:
		return "128"
	if code==4:
		return "128-WRL SIM300"
	if code==132:
		return "128-WRL LEON"
	if code==66:
		return "64 PLUS"
	if code==67:
		return "128 PLUS"
	return "UNKNOWN"

''' Gets the firmware version as reported by panel, language and whether settings has been copied to flash
again - I only check if language is English or other
''' 
def iVersion():
	resp=sendcommand("7E")
	model="INTEGRA "+hardwareModel(resp[0])
	version=format("%c.%c%c %c%c%c%c-%c%c-%c%c" % tuple([chr(x) for x in resp[1:12]]))
	if resp[12]==1:
		language="English"
	else:
		language="Other"

	if resp[13]==255:
		settings="stored"
	else:
		settings="NOT STORED"
	print (model, version, "LANG: "+language,"SETTINGS "+settings+" in flash")

''' Gets the Integra time. Unfortunately, it is being sent in a rather wierd format, hence the mess below
'''
def iTime():
	r=sendcommand("1A")
	itime=ihex(r[0])+ihex(r[1])+"-"+ihex(r[2])+"-"+ihex(r[3])+" "+ihex(r[4])+":"+ihex(r[5])+":"+ihex(r[6])
	return itime

''' Gets name of the zone and output. Could be easily extended to get name of users, expanders and so on
'''
def iName(number,devicetype):
	number=str(hex(number))[2:]
	if len(number)==1:
		number="0"+number
	r=sendcommand("EE"+devicetype+str(number))
	return r[3:].decode("ascii")

''' Checks violated zones. This make separate calls to get name of the violated zones. In a real life software,
this should be cached and synchronised when data are change (i.e. rarely, as zones, outputs et ceterea usually 
keep their names for a long time). In this demo, the more enabled outputs you have, the longer this script  will
take to execute
''' 
def iViolation():
	r=sendcommand("00")
	v=""
	for i in range(0,15):
		for b in range(0,7):
			if 2**b	& (r[i]):
				wait()
				v+=str(8*i+b+1)+" "+iName(8*i+b+1,ZONE)+":*\n"
	print (v)

''' Checks enabled outputs. See the comment for iViolation
'''				
def iOutputs():
	r=sendcommand("17")
	o=""
	for i in range(0,15):
		for b in range(0,7):
			if 2**b	& r[i]:
				wait()
				o+=str(8*i+b+1)+" "+iName(8*i+b+1,OUTPUT)+": ON\n"
	print (o)

''' Returns arm status for the partition (true: armed, false: disarmed)
'''
def iArmStatus(partition):
	r=sendcommand("0A")
	if 2**(partition % 8)  & r[partition>>3]:
		return True
	else:
		return False



#### BASIC DEMO
''' ... and now it is the time to demonstrate what have we learnt today
'''
if len(sys.argv)<2:
	print ("Execution: %s IP_ADDRESS_OF_THE_ETHM1_MODULE" % sys.argv[0],  file=sys.stderr)
	sys.exit(1)

host=sys.argv[1]

iVersion()
wait()
print ("Integra time: "+iTime())
wait()
partname=iName(1,PARTITION)
wait()
print ("%s armed: %s" % (partname,iArmStatus(0)))
wait()
print ("Violated zones:")
iViolation()
wait()
print ("Active outputs:")
iOutputs()
print ("Thanks for watching.")

