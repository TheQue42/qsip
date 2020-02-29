#!/usr/bin/env python3
import requests
from urllib.parse import urljoin
import sys
import json
import os

try:
    username = os.environ["UNIFI_ADMIN"]
    password = os.environ["UNIFI_ADMIN_PASS"]
except:
    print("You need to:\n source getUnifiPass.sh")
    sys.exit(1)

cloud_key_ip = "10.9.24.22"
controller_port = 8443
site_name = "default"

base_url = "https://{cloud_key_ip}:{controller_port}".format(
    cloud_key_ip=cloud_key_ip, controller_port=controller_port
)

# How many do you have to forget?
#
# The API call is a **POST** to `/api/s/{site}/cmd/stamgr` with the body `{"macs":["00:1e:35:ff:ff:ff"],"cmd":"forget-sta"}` yes, it does look like you could submit them all in bulk to the API but the webUI doesn't expose that
#
# To fetch the list of all devices in json **GET** `/api/s/{site}/stat/alluser`
#
# Shouldn't be that hard to throw something together in python.


def api_login(sess, base_url):
    payload = {"username": username, "password": password}
    url = urljoin(base_url, "/api/login")
    resp = sess.post(url, json=payload, headers={"Referer": "/login"})
    if resp.status_code == 200:
        print("[*] successfully logged in")
        return True
    else:
        print("[!] failed to login with provided credentials")
        return False


def api_get_clients(sess, base_url, site_name):
    url = urljoin(
        base_url, "/api/s/{site_name}/stat/alluser".format(site_name=site_name)
    )
    resp = sess.get(url)
    client_list = resp.json()["data"]
    print("[*] retreived client list:", len(client_list))
    return client_list


def api_del_clients(sess, base_url, site_name, macs):
    payload = {"cmd": "forget-sta", "macs": macs}
    url = urljoin(base_url, "/api/s/{site_name}/cmd/stamgr".format(site_name=site_name))
    print("Post Payload", payload)
    resp = sess.post(url, json=payload)
    client_list = resp.json()["data"]
    json.dumps(resp.json(), indent=2, sort_keys=True, ensure_ascii=False)
    print(f'\nPurged Clients Completed With: {resp.status_code}. MacsIn: {len(macs)}, MacsReturned: {len(client_list)}')
    return client_list

class Color:
    D="\033[0m";
    BOLD="\033[1m";
    UNBOLD="\033[22m";
    RED="\033[31m";
    GREEN="\033[32m";
    YELLOW="\033[33m";
    BLUE="\033[34m";
    PINK="\033[35m";
    CYAN="\033[36m";
    WHITE="\033[37m";

import time,re
def client_macs(client_list):
    macs = []
    cKeys=  []
    #All keys: {'name', 'rx_packets', 'tx_packets', '_id', 'tx_bytes', 'is_guest', 'usergroup_id', 'last_seen', 'hostname', 'mac', 'is_wired', 'duration', 'rx_bytes', 'wifi_tx_attempts', 'oui', 'site_id', 'note', 'first_seen', 'noted', 'tx_retries'}
    keysToList=['hostname', 'name', 'is_wired', 'rx_bytes', 'tx_bytes', 'duration', 'rx_packets']
    for client in client_list:
        clientKeys = list(client.keys())
        cKeys = set(list(cKeys) + clientKeys)
        InfoStringToPrintForEachMac = ""
        for k in keysToList:
            if k in client:
                #Id:(04:d6:aa:1a:73:9b) hostname:                Yoda,name:              YodaS8,is_wired:               False,rx_bytes:          1029143068,tx_bytes:          5750289955,noted:                True,
                if re.search("name", k):
                    InfoStringToPrintForEachMac = InfoStringToPrintForEachMac + "{}:{:<24s},".format(Color.BOLD + k + Color.D, str(client[k])) 
                else:
                    InfoStringToPrintForEachMac = InfoStringToPrintForEachMac + "{}:{:<14s},".format(Color.BOLD + k + Color.D, str(client[k])) 
            else:
                if re.search("name", k):
                    InfoStringToPrintForEachMac = InfoStringToPrintForEachMac + "{}:{:<24s},".format(Color.BOLD + k + Color.D, "[]") 
                else:
                    InfoStringToPrintForEachMac = InfoStringToPrintForEachMac + "{}:{:<14s},".format(Color.BOLD + k + Color.D, "[]") 
                #InfoStringToPrintForEachMac = InfoStringToPrintForEachMac + "{}:{:<24s},".format(k, "[]") 
        hostnameEmpty = True if "hostname" not in client.keys() or client["hostname"] == "" else False
        nameEmpty = True if "name" not in client.keys() or client["name"] == "" else False
        if (hostnameEmpty and nameEmpty and
            "tx_packets" not in client and "rx_packets" not in client):
            first = time.localtime(client["first_seen"])
            last = first = time.localtime(client["last_seen"])
            print(f'{Color.RED}{Color.BOLD}Bad{Color.D}:{client["mac"]} {InfoStringToPrintForEachMac}', " First:", time.strftime("%b%a%d %H:%M", first), "  LastSeen:", time.strftime("%b%a%d %H:%M", last),f"{Color.D}" )
            macs.append(client["mac"])
        else:
            print(f'Mac:{client["mac"]}', InfoStringToPrintForEachMac)
        
        if ("use_fixedip" not in client and
            ("tx_packets" in client and client["tx_packets"] == 0)
            and ("rx_packets" in client and client["rx_packets"] == 0)
            and "mac" in client ):
            #print(f'Appending Mac: {client["mac"]}')
            macs.append(client["mac"])
            
    print("[*] {!s} clients identified for purge".format(len(macs)))
    #print("All keys found:", cKeys)
    removeDuplicates = set(macs)
    macs = list(removeDuplicates)
    return macs

## TODO: Params --printGood -q
if __name__ == "__main__":
    sess = requests.Session()
    sess.verify = False
    requests.packages.urllib3.disable_warnings()
    #print("Params", sys.argv)
    success = api_login(sess=sess, base_url=base_url)
    if success:
        client_list = api_get_clients(sess=sess, base_url=base_url, site_name=site_name)
        macs = client_macs(client_list=client_list)
        if len(macs) == 0: 
            print("No Macs identified for purge")
        else:
            if len(sys.argv) > 1 and sys.argv[1] == "--delete":
                api_del_clients(sess=sess, base_url=base_url, site_name=site_name, macs=macs)
            else:
                print("--delete not specified, skipping delete")
