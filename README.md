# OCI-OCVS-VLAN
Automation tool for VLAN management for OCI / OCVS environments

Created by: richard.garsthagen@oracle.com

Important; Make sure you already have setup the OCI-CLI with the correct credentials.

This script will create VLANs and attaches them to all ESXi hosts in an SDDC.

### Usage:

pyhton create-vlans.py -s SDDC_OCID -f VLAN_FILE

### Example:

python create-vlans.py -s ocid1.vmwaresddc.oc1.eu-frankfurt-1.xxxxxxxxxxxxxx -f vlans 


The specified vlans file should contain for each vlan 1 line in the file. 
Each vlan entry contain (comma seperated):
- vnic index (the ID of the physical network card), this should be a 0 or 1
- vlan id
- cidr range (this must be inside VCN cidr range, but can be a "dummy" range, meaning it does not have to relate to the actual cidr range used inside VMware)

See also: enclosed vlans example file