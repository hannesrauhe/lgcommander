#!/usr/bin/env python3

import http.client
import xml.etree.ElementTree as etree
import socket
import re
import sys
lgtv = {}

dialogMsg =""
headers = {"Content-Type": "application/atom+xml"}
lgtv["pairingKey"] = "000000"

def getip():
    strngtoXmit =   'M-SEARCH * HTTP/1.1' + '\r\n' + \
                    'HOST: 239.255.255.250:1900'  + '\r\n' + \
                    'MAN: "ssdp:discover"'  + '\r\n' + \
                    'MX: 2'  + '\r\n' + \
                    'ST: urn:schemas-upnp-org:device:MediaRenderer:1'  + '\r\n' +  '\r\n'

    bytestoXmit = strngtoXmit.encode()
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    sock.settimeout(3)
    found = False
    gotstr = 'notyet'
    i = 0
    ipaddress = None
    sock.sendto( bytestoXmit,  ('239.255.255.250', 1900 ) )
    while not found and i <= 5 and gotstr == 'notyet':
        try:
            gotbytes, addressport = sock.recvfrom(512)
            gotstr = gotbytes.decode()
        except:
            i += 1
            sock.sendto( bytestoXmit, ( '239.255.255.250', 1900 ) )
        if re.search('LG', gotstr):
            ipaddress, _ = addressport
            found = True
        else:
            gotstr = 'notyet'
        i += 1
    sock.close()
    if not found : sys.exit("Lg TV not found")
    return ipaddress


def displayKey():
    conn = http.client.HTTPConnection( lgtv["ipaddress"], port=8080)
    reqKey = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthKeyReq</type></auth>"
    conn.request("POST", "/roap/api/auth", reqKey, headers=headers)
    httpResponse = conn.getresponse()
    if httpResponse.reason != "OK" : sys.exit("Network error")
    return httpResponse.reason


def getSessionid():
    conn = http.client.HTTPConnection( lgtv["ipaddress"], port=8080)
    pairCmd = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type><value>" \
            + lgtv["pairingKey"] + "</value></auth>"
    conn.request("POST", "/roap/api/auth", pairCmd, headers=headers)
    httpResponse = conn.getresponse()
    if httpResponse.reason != "OK" : return httpResponse.reason
    tree = etree.XML(httpResponse.read())
    return tree.find('session').text


def getPairingKey():
    displayKey()
    dialogMsg = "Please enter the pairing key\nyou see on your TV screen\n"
    result = input(dialogMsg)
    lgtv["pairingKey"] = result

def handleCommand(cmdcode):
    conn = http.client.HTTPConnection( lgtv["ipaddress"], port=8080)
    cmdText = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command>" \
                + "<name>HandleKeyInput</name><value>" \
                + cmdcode \
                + "</value></command>"
    conn.request("POST", "/roap/api/command", cmdText, headers=headers)
    httpResponse = conn.getresponse()


#main()

lgtv["ipaddress"] = getip()
theSessionid = getSessionid()
while theSessionid == "Unauthorized" :
    getPairingKey()
    theSessionid = getSessionid()

if len(theSessionid) < 8 : sys.exit("Could not get Session Id: " + theSessionid)

lgtv["session"] = theSessionid


dialogMsg =""
for lgkey in lgtv :
    dialogMsg += lgkey + ": " + lgtv[lgkey] + "\n"

dialogMsg += "Success in establishing command session\n"
dialogMsg += "=" * 28 + "\n"
dialogMsg += "Enter command code i.e. a number between 0 and 1024\n"
dialogMsg += "Enter a number greater than 1024 to quit.\n"


result = "91"
while int(result) < 1024:
    result = input(dialogMsg)
    handleCommand(result)

sys.exit(0)