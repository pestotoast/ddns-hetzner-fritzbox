# ddns-hetzner-fritzbox

This Python script performs several tasks related to updating DNS records for a domain managed by Hetzner's DNS service. The script uses the Hetzner DNS API and the Universal Plug and Play (UPnP) protocol to communicate with a Fritz!Box router to retrieve the external IP address of the router. It then updates the corresponding DNS record for the domain with the new IP address. If the DNS-Record do not exist yet they will be created automatically.

- Creates and Updates your A and AAAA records for Domains Hosted at dns.hetzner.com
- Asks your router for your public IP instead of relying on an external service
- Easy configuration, only the domain name and the Hetzner-API-Token is required
- Works only with AVM FritzBox Routers, you need to enable UPnP-Access for your local network (should be enabled by default)

### Configuration

```
domain_name: required
api_token: required

## default configuration:
#ttl: 60
#ip_check_interval: 60
## Instead of asking external services for our public ip we ask our router
#fritzbox_ip: 192.168.178.1
## leave this empty if you dont care about IPv6:
#ipv6_interface_id: ::dead:beef
```
### Running in Docker (recommended):
You can run the script with the included docker-compose File
```
version: '3'
services:
  ddns:
    image: pestotoast/dyndns-hetzner-fritzbox
    restart: always
    volumes:
      - ./config.yml:/config.yml
```


### Installtion/Running the script manually:
Install dependencies (on Ubuntu):

```
sudo apt install python-requests pyyaml
```
OR using pip:

```
pip install requests pyyaml
```
the edit your config.yml and start the script:

```
./ddns.py -c config.yml
```
