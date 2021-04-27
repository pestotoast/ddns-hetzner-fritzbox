#!/usr/bin/python3
import requests
import time
import json
import os
import datetime
import xml.etree.ElementTree as ET

def getIPv4():
    url = 'http://' + fritzbox_ip + ':49000/igdupnp/control/WANIPConn1'
    headers = { 'content-type': 'text/xml; charset="utf-8', 'SOAPAction': 'urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress'}        
    data = '<?xml version=\"1.0\" encoding=\"utf-8\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"> <s:Body> <u:GetExternalIPAddress xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\" /></s:Body></s:Envelope>'
    response = requests.post(url, data=data, headers=headers)
    xml = ET.fromstring(response.text)
    return xml[0][0][0].text

def getIPv6():
    url = 'http://' + fritzbox_ip + ':49000/igdupnp/control/WANIPConn1'
    headers = { 'content-type': 'text/xml; charset="utf-8', 'SOAPAction': 'urn:schemas-upnp-org:service:WANIPConnection:1#X_AVM_DE_GetIPv6Prefix'}        
    data = '<?xml version=\"1.0\" encoding=\"utf-8\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"> <s:Body> <u:X_AVM_DE_GetIPv6Prefix xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\" /></s:Body></s:Envelope>'
    response = requests.post(url, data=data, headers=headers)
    xml = ET.fromstring(response.text)
    return xml[0][0][0].text + "2"

def updateIPv4(input):
    url = 'https://dns.hetzner.com/api/v1/records/' + input["recordId_v4"]
    headers = { 'Content-Type': 'application/json', 'Auth-API-Token': input["token"]}
    data = { 'value': input["ip4"], 'ttl': 60, 'type': 'A', 'name': '@', 'zone_id': input["zoneId"]}
    respone = requests.put(url, data=json.dumps(data), headers=headers)
    print(respone.text)

def updateIPv6(input):
    url = 'https://dns.hetzner.com/api/v1/records/' + input["recordId_v6"]
    headers = { 'Content-Type': 'application/json', 'Auth-API-Token': input["token"]}
    data = { 'value': input["ip6"], 'ttl': 60, 'type': 'AAAA', 'name': '@', 'zone_id': input["zoneId"]}
    respone = requests.put(url, data=json.dumps(data), headers=headers)
    print(respone.text)

fritzbox_ip = os.getenv("FRITZ_BOX_IP","192.168.178.1")
token = os.getenv("HETZNER_API_TOKEN")
domain_1 = os.getenv("DOMAIN_1")
domain_2 = os.getenv("DOMAIN_2")
domain_1 = json.loads(domain_1)
domain_2 = json.loads(domain_2)

dictionary = { 'ip4':'', 'ip6':'' }

print(json.dumps(dictionary))
while 1==1:
    ip4 = getIPv4()
    ip6 = getIPv6()
    domain_1["ip4"] = ip4
    domain_1["ip6"] = ip6
    domain_1["token"] = token

    domain_2["ip4"] = ip4
    domain_2["ip6"] = ip6
    domain_2["token"] = token
    
    if ip4 != dictionary["ip4"] or ip6 != dictionary["ip6"]:
        print(datetime.datetime.now())
        try:
          updateIPv4(domain_1)
          updateIPv6(domain_1)
          updateIPv4(domain_2)
          updateIPv6(domain_2)
          dictionary["ip4"] = ip4
          dictionary["ip6"] = ip6
        except:
          dictionary["ip4"] = ''
          dictionary["ip6"] = ''
        print(json.dumps(dictionary))
    time.sleep(60)
