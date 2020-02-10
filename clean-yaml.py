#!/usr/bin/env python3

import json
import os, sys, re
import argparse

_scriptVersion=0.01

def _createArgParser():
    cli = argparse.ArgumentParser(
            prog="PythonProg",
            description = "Default Description",
            epilog="This is a python script",
            )

    cli.add_argument('--version', "-V", action='version', version=F'%(prog)s {_scriptVersion}')
    cli.add_argument("--noop", "-n",  help="Just show what will be done", action='store_true')

    cli.add_argument('--infile', "-i", nargs='?', default=sys.stdin)    #, type=argparse.FileType('r')
    #cli.add_argument('--out', "-o", nargs='?', default=sys.stdout)  #type=argparse.FileType('w')

    cli.add_argument('--zerocount', "-zc", default=3)
    
    whatDoFilter = cli.add_mutually_exclusive_group() # required=true if either cli-param is required
    whatDoFilter.add_argument('--strip_unifi', nargs='?', default="dont", const="only empty", help="strip (all?) unifi nodes from core_entities")
    whatDoFilter.add_argument('--list_unifi', nargs='?', default="dont", const="only empty", help="list unifi nodes from core_entities")
    whatDoFilter.add_argument('--del_node', "-dn", type=int, help="del specfic node id")
    whatDoFilter.add_argument('--list_node', "-ln", type=int, help="del specfic node id")
    whatDoFilter.add_argument('--list-disabled', "-ld", action="store_true", help="List disabled (entities)")
    
    
    loggingDebug = cli.add_mutually_exclusive_group() # required=true if either cli-param is required
    loggingDebug.add_argument("--verbose", "-v", help="Increase verbosity", action='count')
    loggingDebug.add_argument("--quiet", "-q", help="Reduce verbosity", action='count')
    return cli



def printEntity(e, e_id, all_meta=False):
    for entity_key in e.keys():
        if re.match(r"unique_id|config_entry_id|device_id", entity_key) and not all_meta:
            continue
        print("[%s] Key: %s has value: [%s]" % (e_id, entity_key, e[entity_key]))
    print("")


def processEntities(args, jsonData):
    '''
    Process /var/lib/home-assistant/.storage/core.entity_registry
    '''
    fullCount = 0
    unifiCount = 0
    deleteCount = 0
    filteredData = dict()
    filteredData["data"] = dict()
    filteredData["data"]["entities"] = []
    deleteData = dict()
    deleteData["data"] = dict()
    deleteData["data"]["entities"] = []

    origCount = len(jsonData["data"]["entities"])

    if args.list_node :
        for entity in jsonData["data"]["entities"] :
            filterString1 = str(args.list_node) + "-"
            filterString2 = "node-" + str(args.list_node)
            if re.match(filterString1, entity["unique_id"]) or re.match(filterString2, entity["unique_id"]) :
                #printEntity(entity, fullCount, all_meta=True)
                print(json.dumps(entity, indent=1))
                print("")
                fullCount += 1

    if args.del_node :
        for entity in jsonData["data"]["entities"] :
            filterString1 = str(args.del_node) + "-"
            filterString2 = "node-" + str(args.del_node)
            if re.match(filterString1, entity["unique_id"]) or re.match(filterString2, entity["unique_id"]) :
                deleteData["data"]["entities"].append(entity)
                print(json.dumps(entity, indent=1))
                print("")
                deleteCount += 1
            else:
                filteredData["data"]["entities"].append(entity)
                fullCount +=1
        afterFile = open("/tmp/after.yaml", "w")
        delFile = open("/tmp/deleted.yaml", "w")
        print("-------------------")
        print("Filterd Count: {}, Deleted Count: {}, Original Count: {}".
                format(fullCount, deleteCount, origCount))
        json.dump(filteredData, afterFile, indent=2, sort_keys=True)
        afterFile.close()
        json.dump(deleteData, delFile, indent=2, sort_keys=True)
        delFile.close()

    if args.list_disabled : # Disabled_by is not empty 
        for entity in jsonData["data"]["entities"] :
            if entity["disabled_by"] :
                printEntity(entity, fullCount)
                print("")
                fullCount += 1
    
    if args.list_unifi != "dont" :
        for entity in jsonData["data"]["entities"] :
            if entity["platform"] == "unifi":
                # Should we only display the known2empty and is it one of those?
                if re.match(r"only", args.list_unifi) :
                    if re.match(r"device_tracker.unifi.*", entity["entity_id"]):
                        printEntity(entity, fullCount)
                        unifiCount += 1
                else :
                    printEntity(entity, fullCount)                                            
                fullCount += 1
        print("All Unifi Count: {}, Filtered Unifi Count: {}".format(fullCount, unifiCount))


    if args.strip_unifi != "dont" :
        '''
        here we've got entities[] with keys:
        - "config_entry_id": "7bfa7234010b419f956f6dbb9d72e966",
        - "device_id": "9f718999a08345db9123fd20c929344c",
        - "disabled_by": "user",
        - "entity_id": "sensor.fibaro_system_fgms001_zw5_motion_sensor_seismic_intensity",
        - "entity_id": "device_tracker.unifi_58_ef_39_a8_3a_9e_default",        
        - "name": "MS - Mancave - Seismic",
        - "platform": "zwave",
        - "unique_id": "3-72057594093257106"
        '''
        print("Will strip {} Unifi entries".format(args.strip_unifi))
        for entity in jsonData["data"]["entities"] :
            if entity["platform"] == "unifi" :
                # Should we only strip the empty, know-2-bad entries?
                if re.match(r"only", args.strip_unifi) and not re.match(r"device_tracker.unifi.*", entity["entity_id"]):
                    print("Adding: {} with name: {}".format(entity["entity_id"], entity["name"]))
                    filteredData["data"]["entities"].append(entity)
                    unifiCount += 1
            else:
                filteredData["data"]["entities"].append(entity)
            fullCount +=1
    
        print("Filtered list count: {}, Orig List Count: {}, Unifi Count: {}".
                format(len(filteredData["data"]["entities"]), origCount, unifiCount))
        newFile = open("/tmp/newfile.yaml", "w")
        print("-------------------")
        json.dump(filteredData, newFile, indent=2, sort_keys=True)
        newFile.close()
        print("-------------------")



def main(argv = None):
    _scriptName = sys.argv[0]
    cliArgs = _createArgParser()

    print(f"Arguments Will BE parsed by {sys.argv[0]}, and version:{_scriptVersion}")
    args = cliArgs.parse_args()
    print(args)

    if os.path.isfile(args.infile) :
        try:
            yfile = open(args.infile)
            jsonObj = json.load(yfile)
        except:
            print("Failed to open file")

    if "entities" in jsonObj["data"].keys():
        print("Nr of Entitites: " + str(len(jsonObj["data"]["entities"])) )
        processEntities(args, jsonObj)
    elif "devices" in jsonObj["data"].keys():
        print("Nr Of Devices: " + str(len(jsonObj["data"]["devices"])))
    else :
        print("Unknown contents in file")
        
        
if __name__ == "__main__":
    sys.exit(main())


#f = open("/var/lib/ha/.storage/core.entity_registry")

