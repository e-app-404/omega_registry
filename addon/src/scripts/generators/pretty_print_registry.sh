#!/bin/bash
# Pretty-print omega_registry_master.json after generation
python3 -m json.tool canonical/omega_registry_master.json > canonical/alias/omega_registry_master.pretty.json
