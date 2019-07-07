import base64
import argparse
import json
from urllib.parse import urlencode
from urllib.request import urlopen,Request
import xml.etree.ElementTree as etree

def fetch_external_ip(type):
    url = 'https://' + ("api6" if type == "AAAA" else "api") + '.ipify.org'
    ip = urlopen(url).read().decode('utf-8')[:-1]
    return ip

if __name__ == "__main__":
    try:
        from config import CONFIG
    except ImportError:
        print("Error: config.py NOT found")
        exit()

    # Show all arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ttl', default='300', help='Time To Live')
    parser.add_argument('--type', default='AAAA', help='Type of record: A for IPV4 or AAAA for IPV6')
    parser.add_argument('--ip', help='The IPV4/IPV6 address (if known)')
    parser.add_argument('--value', help='The value of the TXT (if known)')
    parser.add_argument('--name', help='Your record name, ie: ipv6.domain.com', required=True)
    parser.add_argument('--domain', help='The domain name containing the record name', required=True)
    args = parser.parse_args()

    # Generate a auth_string to connect to cPanel
    auth_string = 'Basic ' + base64.b64encode((CONFIG['username']+':'+CONFIG['password']).encode()).decode("utf-8")

    domain = args.domain
    record = args.name
    if not record.endswith('.'):
        record += "."
    type = "A"
    if args.type.upper() == "AAAA" or args.type.upper() == "TXT":
        type = args.type.upper()
    ip = args.ip if args.ip != None else fetch_external_ip(type)
    ttl = args.ttl
    value = args.value if args.value != None else ""

    # Fetch existing DNS records
    q = Request(CONFIG['url'] + '/json-api/cpanel?cpanel_jsonapi_module=ZoneEdit&cpanel_jsonapi_func=fetchzone&cpanel_jsonapi_apiversion=2&domain=' + domain + '&type=' + type)
    q.add_header('Authorization', auth_string)

    # Load and Parse the records to find if the record already exists
    records = json.loads(urlopen(q).read().decode("utf-8"))['cpanelresult']['data'][0]['record']

    line = "0"
    for json_record in records:
        if json_record['name'] != None and json_record['name'] == record:
            line = str(json_record['line'])
            break

    # Update or add the record
    query = "&address=" + ip
    if type == "TXT":
        query = "&" + urlencode( {'txtdata': value} )

    url = CONFIG['url'] + "/json-api/cpanel?cpanel_jsonapi_module=ZoneEdit&cpanel_jsonapi_func=" + ("add" if line == "0" else "edit") + "_zone_record&cpanel_jsonapi_apiversion=2&domain="+ domain + "&name=" + record + "&type=" + type + "&ttl=" + ttl + query
    if line != "0":
        url += "&Line=" + line

    q = Request(url)
    q.add_header('Authorization', auth_string)
    json_response = json.loads(urlopen(q).read().decode("utf-8"))

    # parse and print pretty
    print(json.dumps(json_response, indent=4))
