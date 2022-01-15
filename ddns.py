#!/usr/bin/env python3
import requests
import time
import json
import yaml
import datetime
import sys
import xml.etree.ElementTree as ET

def getIPv4(fritzbox_ip):
  url = 'http://' + fritzbox_ip + ':49000/igdupnp/control/WANIPConn1'
  headers = { 'content-type': 'text/xml; charset="utf-8', 'SOAPAction': 'urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress'}        
  data = '<?xml version=\"1.0\" encoding=\"utf-8\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"> <s:Body> <u:GetExternalIPAddress xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\" /></s:Body></s:Envelope>'
  response = requests.post(url, data=data, headers=headers)
  xml = ET.fromstring(response.text)
  return xml[0][0][0].text

def getIPv6(fritzbox_ip, ipv6_interface_id):
  url = 'http://' + fritzbox_ip + ':49000/igdupnp/control/WANIPConn1'
  headers = { 'content-type': 'text/xml; charset="utf-8', 'SOAPAction': 'urn:schemas-upnp-org:service:WANIPConnection:1#X_AVM_DE_GetIPv6Prefix'}        
  data = '<?xml version=\"1.0\" encoding=\"utf-8\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"> <s:Body> <u:X_AVM_DE_GetIPv6Prefix xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\" /></s:Body></s:Envelope>'
  response = requests.post(url, data=data, headers=headers)
  xml = ET.fromstring(response.text)
  interface = ipv6_interface_id.replace('::', '')
  return xml[0][0][0].text + interface

def updateRecord(ip_address, ttl, record, api_token):
  url = 'https://dns.hetzner.com/api/v1/records/' + record['id']
  headers = { 'Content-Type': 'application/json', 'Auth-API-Token': api_token}
  data = {  'value': ip_address, 
            'ttl': ttl,
            'type': record['type'], 
            'name': record['name'], 
            'zone_id': record['zone_id']}
  respone = requests.put(url, data=json.dumps(data), headers=headers)
  log(respone.text)

def getRecord(record_type, record_name, zone_id, api_token):
  response = requests.get(
      url="https://dns.hetzner.com/api/v1/records",
      params={ "zone_id": zone_id },
      headers={ "Auth-API-Token": api_token },
  )
  if response.status_code != 200:
    raise Exception('Failed to get zone records: {status_code}'.format(status_code=response.status_code))
  records = json.loads(response.text)      
  for record in records['records']:
    if record['name'] == record_name and record['type'] == record_type:
      return record

def createRecord(ip_address, ttl, record_type, record_name, zone_id, api_token):
  response = requests.post(
          url="https://dns.hetzner.com/api/v1/records",
          params={ "zone_id": zone_id },
          headers={ "Auth-API-Token": api_token },
           data=json.dumps({
                "value": ip_address,
                "ttl": ttl,
                "type": record_type,
                "name": record_name,
                "zone_id": zone_id
            })
      )
  if response.status_code != 200:
    raise Exception('Failed to create record: {reason}'.format(reason=response.reason))
  record = json.loads(response.text)
  return record['record']
  
def getZone(domain_name, api_token):
  response = requests.get(
    url="https://dns.hetzner.com/api/v1/zones",
    headers={ "Auth-API-Token": api_token },
  )
  if response.status_code != 200:
    raise Exception('Failed to get zone: {reason}'.format(reason=response.reason))
  zones = json.loads(response.text)      
  for zone in zones['zones']:
    if zone['name'] in domain_name :
      return zone
  raise Exception("Could not find zone")

def loadConfig(path):
  try:
    with open(path, "r") as ymlfile:
      conf = yaml.safe_load(ymlfile)
      ymlfile.close()
    if not 'domain_name' in conf or conf['domain_name'] == '':
      log("Please add your 'domain_name' to the configuration file")
      exit(1)
    if not 'api_token' in conf or conf['api_token'] == '':
      log("Please add your 'api_token' to the configuration file. You can create it at https://dns.hetzner.com/settings/api-token")
      exit(1)
    if not 'ttl' in conf or conf['ttl'] == '':
      conf['ttl'] = 60
    if not 'ip_check_interval' in conf or conf['ip_check_interval'] == '':
      conf['ip_check_interval'] = 60
    if not 'fritzbox_ip' in conf or conf['fritzbox_ip'] == '':
      conf['fritzbox_ip'] = "192.168.178.1"
    if (not 'ipv6_interface_id' in conf) or conf['ipv6_interface_id'] == '': 
      conf['ipv6_interface_id'] = "disabled"
    return conf
  except FileNotFoundError:
    log("No such file or directory: " + path)
    exit(1)

def getSubdomain(domain_name):
    strings = domain_name.split('.')
    #remove empty field if domain ends with dot
    if strings[-1] == '':
      strings.pop(-1)
    #remove tld
    strings.pop(-1)
    #remove 2nd lvl domain
    strings.pop(-1)
    if not strings:
      return '@'
    if len(strings) > 1:
      return '.'.join(strings)
    return strings[0]

def log(text, newline = True):
  if newline:
    date = str(datetime.datetime.now())
    text = date + " | " +text
    print(text)
  else:
    print(text, end ="")

def updateLoop(conf, record_v4, record_v6):
  log("Starting update check, running every " + str(conf['ip_check_interval']) + " seconds..")
  ip4=old_ip4=ip6=old_ip6=''
  counter=0
  if record_v4:
    ip4=old_ip4=record_v4['value']
  if record_v6: 
    ip6=old_ip6=record_v6['value']
  while True:    
    if counter % 10 == 0:
      log("Comparing records at hetzner.. ", False)
      old_ip4 = getRecord(record_v4['type'], record_v4['name'], record_v4['zone_id'], conf['api_token'])['value']
      if not record_v6 is None:
        old_ip6 = getRecord(record_v6['type'], record_v6['name'], record_v6['zone_id'], conf['api_token'])['value']
      if ip4 == old_ip4 or ip6 == old_ip6:
        log("Everything up-to-date :)")
  
    ip4 = getIPv4(conf['fritzbox_ip'])
    if conf['ipv6_interface_id'] != 'disabled':
      ip6 = getIPv6(conf['fritzbox_ip'], conf['ipv6_interface_id'])      
    if ip4 != old_ip4 or ip6 != old_ip6:
        log('###########################')
        log("old: " + old_ip6)
        log("new: " + ip6)
        try:
          if ip4 != old_ip4:
            updateRecord(ip4, conf['ttl'], record_v4, conf['api_token'])
            old_ip4 = ip4
          if ip6 != old_ip6:
            updateRecord(ip6, conf['ttl'], record_v6, conf['api_token'])
            old_ip6 = ip6
        except Exception as e:
          log(e)
          old_ip4=''
          old_ip6=''
        log('###########################')          
    time.sleep(conf['ip_check_interval'])
    counter=counter+1

def init(conf):
  zone = getZone(conf['domain_name'], conf['api_token'])
  log("Found existing zone " + zone['id'] +" for domain: " + zone['name'] )
  record_name = getSubdomain(conf['domain_name'])
  record_v4 = getRecord('A', record_name, zone['id'], conf['api_token'])
  if not record_v4:
    record_v4 = createRecord( getIPv4(conf['fritzbox_ip']),
                              conf['ttl'], 
                              'A', 
                              record_name, 
                              zone['id'], 
                              conf['api_token'])
    log("Added missing record: " + str(record_v4))
  else:
    log("Found existing A-record " + record_v4['id'] + " for: " + conf['domain_name'])
  record_v6=None
  if conf['ipv6_interface_id'] != 'disabled':
    record_v6 = getRecord('AAAA', record_name, zone['id'], conf['api_token'])
    if not record_v6:
      record_v6 = createRecord( getIPv6(conf['fritzbox_ip'], conf['ipv6_interface_id']), 
                                conf['ttl'], 
                                'AAAA', 
                                record_name, 
                                zone['id'], 
                                conf['api_token'])
      log("Added missing record: " + str(record_v6))
    else:
      log("Found existing AAAA-record " + record_v6['id'] + " for: " + conf['domain_name'])
  else:
    log("Skipping IPv6 related tasks. 'ipv6_interface_id' is not set.")
  return record_v4, record_v6

def main():
  try:
    conf = loadConfig(sys.argv[2])
  except IndexError:
    log("""
      Usage: ./dyndns -c config.yml
    """)
    exit(1)
  log("Started DynDNS Client")
  record_v4, record_v6 = init(conf)
  updateLoop(conf, record_v4, record_v6)

if __name__=="__main__":
    main()

