#export FY=filter-yaml.py
rm -f Cleaned.*json*
rm -f Stripped.*json*
filter-yaml.py -e -p entity_id:device_tracker.unifi_ plat:unifi unique_id:default entity_id:default --suffix .1
filter-yaml.py -f Cleaned.entities.json.1 -p "unique_id:[rt]x" entity_id:sensor.none --suffix .2
filter-yaml.py -d -p "name|model|manuf|ident|sw_|via_dev:null" -q --suffix .1
cp Cleaned.devices.json.1  /var/lib/home-assistant/.storage/core.device_registry
cp Cleaned.entities.json.2 /var/lib/home-assistant/.storage/core.entity_registry

