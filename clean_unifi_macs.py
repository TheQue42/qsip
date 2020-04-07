#!/usr/bin/env python3
import requests
from urllib.parse import urljoin
import sys
import json
from json import JSONDecodeError
import os, argparse
import time,re

try:
    username = os.environ["UNIFI_ADMIN"]
    password = os.environ["UNIFI_ADMIN_PASS"]
except:
    print("You need to:\n source getUnifiPass.sh")
    sys.exit(1)

try:
    IsRunningFromCron = os.environ["RUNNING_IN_CRON"]
    cronExecution = True
    class Color:
        D="";
        BOLD="";
        UNBOLD="";
        RED="";
        GREEN="";
        YELLOW="";
        BLUE="";
        PINK="";
        CYAN="";
        WHITE="";
except:
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
    cronExecution = False
#print("Cron is", cronExecution)
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
TotalClients = 0
listUrl = urljoin( base_url, "/api/s/{site_name}/stat/alluser".format(site_name=site_name) )

def api_login(sess, base_url):
    payload = {"username": username, "password": password}
    url = urljoin(base_url, "/api/login")
    resp = sess.post(url, json=payload, headers={"Referer": "/login"})
    if resp.status_code == 200:
        #print("[*] successfully logged in")
        return True
    else:
        #print("[!] failed to login with provided credentials")
        return False


def api_get_clients(sess, base_url, site_name):
    url = listUrl
    resp = sess.get(url)
    client_list = resp.json()["data"]
    if not cronExecution:
        print("[*] retreived client list:", len(client_list))
    return client_list


def api_del_clients(sess, base_url, site_name, macs):
    payload = {"cmd": "forget-sta", "macs": macs}
    url = urljoin(base_url, "/api/s/{site_name}/cmd/stamgr".format(site_name=site_name))
    resp = sess.post(url, json=payload)
    client_list = resp.json()["data"]
    print("HttpDelResponse:", resp, "Json:", resp.json())
    time.sleep(4)
    newClientList = api_get_clients(sess, base_url, site_name)
    if len(newClientList) == TotalClients and not cronExecution:
        print("Seems We didnt change anything", len(newClientList), TotalClients)
    #json.dumps(resp.json(), indent=2, sort_keys=True, ensure_ascii=False)
    if not cronExecution:
        print(f'\nPurged Clients Completed With RspCode: {resp.status_code}.\nMacsIn: {len(macs)}, MacsReturned: {len(client_list)}')
    return client_list



def find_bad_macs(client_list, **kwargs):
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
            if not cronExecution:
                print(f'{Color.RED}{Color.BOLD}Bad{Color.D}:{client["mac"]} {InfoStringToPrintForEachMac}',
                      " First:", time.strftime("%b%a%d %H:%M", first), "  LastSeen:", time.strftime("%b%a%d %H:%M", last),f"{Color.D}" )
            macs.append(client["mac"])
        elif not cronExecution and not ("skip_valid" in kwargs.keys() ):
            print(f'Mac:{client["mac"]}', InfoStringToPrintForEachMac)
        
        if ("use_fixedip" not in client and
            ("tx_packets" in client and client["tx_packets"] == 0)
            and ("rx_packets" in client and client["rx_packets"] == 0)
            and "mac" in client ):
            #print(f'Appending Mac: {client["mac"]}')
            macs.append(client["mac"])
            
    if not cronExecution:
        print("[*] {!s} clients identified for purge".format(len(macs)))
    #print("All keys found:", cKeys)
    removeDuplicates = set(macs)
    macs = list(removeDuplicates)
    return macs

def logMacs(macList: list):
    month = time.strftime("%B")
    montlyLogFileName = "/var/tmp/macsCleaned_" + month + ".log"
    dateKey = time.strftime("%b%a%d")
    existingMacs = []
    try:
        # Since  we first want to read, then overwrite from start, we'll have to do open() twice..fseek(?)
        logFile = open(montlyLogFileName, "r")
        # If the file exists, it should contain something
        # file_info = os.stat(montlyLogFileName)
        # if file_info.st_size != 0:
        macAddressLogs = {}
        macAddressLogs = json.load(logFile)
        #myDump = json.dumps(macAddressLogs, indent=2, sort_keys=True, ensure_ascii=False)
        #print("Debug\n", myDump)
        existingMacs = macAddressLogs[dateKey] if dateKey in macAddressLogs.keys() else []
        #print(f"Found {len(existingMacs)} existing (for today) macs, in the logfile: [{montlyLogFileName}]. "
        #        f"Trying to add {len(macList)} more")
        logFile.close()
    except OSError as err:
        print(f"OS Error {err}:", montlyLogFileName)
    except JSONDecodeError as err:
        print(f"JsonError Error {err}, file:", montlyLogFileName)
    try:
        # Truncate file, we've read from it.
        logFile = open(montlyLogFileName, "w")
        #macAddressLogs = {}
        #macAddressLogs[dateKey] = []
    except OSError as err:
        file_info = os.stat(montlyLogFileName)
        print(f"OS Error {err}:", montlyLogFileName, file_info)
        os.unlink(montlyLogFileName)
        sys.exit()

    macs = set(existingMacs+macList)
    macAddressLogs[dateKey] = list(macs)
    #myDump = json.dumps(macAddressLogs, indent=2, sort_keys=True, ensure_ascii=False)
    #print(myDump)
    json.dump(macAddressLogs, logFile, indent=2, sort_keys=True, ensure_ascii=False)
    logFile.close()

## TODO: Params --printGood -q
if __name__ == "__main__":
    sess = requests.Session()
    sess.verify = False
    requests.packages.urllib3.disable_warnings()
   # print("Params", sys.argv)
    cli = argparse.ArgumentParser(
        # prog="Ha-Storage-Filter",
        description="Clean unifi db via http api calls",
        epilog="""
            Use this program at your OWN RISK. For safety sake, it will never overwrite the original files.
            """)

    # cli.add_argument('--singleParam', "-l", help="listOnly", default="")
    # cli.add_argument('--intParam', "-nc", default=3)
    cli.add_argument('--list-only', "-l", action="store_true", default=False)
    cli.add_argument('--skip-valid', "--sd", "--skip_defined", action="store_true")
    cli.add_argument('--dry-run', "-n", action="store_true", default=False)
    args = cli.parse_args()
    #print("Listonly:", args.list_only)
    success = api_login(sess=sess, base_url=base_url)

    if success:
        client_list = api_get_clients(sess=sess, base_url=base_url, site_name=site_name)
        TotalClients = len(client_list)
        macs = find_bad_macs(client_list=client_list, skip_valid=(args.skip_valid))
        if len(macs) == 0 and not cronExecution:
            print("No Macs identified for purge")
        else:
            maxCount = 8
            logMacs(macs)
            while (len(macs) > 0 and maxCount >0 and not args.list_only):
                deleteReturn = api_del_clients(sess=sess, base_url=base_url, site_name=site_name, macs=macs)
                if not cronExecution:
                    print(f"DelReturn {len(deleteReturn)}, LoopCount: {maxCount}")
                time.sleep(15.0+(10.0-maxCount))
                client_list = api_get_clients(sess=sess, base_url=base_url, site_name=site_name)
                TotalClients = len(client_list)
                macs = find_bad_macs(client_list=client_list)
                if not cronExecution:
                    print("TotalClientList", len(client_list), "BadMacs:", len(macs))
                maxCount = maxCount - 1
                # TODO: Store these bad bacs somewhere for stats
            if len(macs) > 0 and maxCount < 1:
                print(f"Attempted Clean {maxCount} times and failed. TotalClients{TotalClients}, BadMacs:{len(macs)}")
                print("Macs:", macs)



