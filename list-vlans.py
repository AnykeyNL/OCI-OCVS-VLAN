import oci
import sys, getopt
import operator

#Location of config file
configfile = "~/.oci/config"

config = oci.config.from_file(configfile)
compute = oci.core.ComputeClient(config)
esxi = oci.ocvp.EsxiHostClient(config)
network = oci.core.VirtualNetworkClient(config)

SDDC_OCID = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:", [""])
except getopt.GetoptError:
    print ("list-vlans.py -s <SDDC OCID>")
    sys.exit(2)

for opt, arg in opts:
    if opt == "-s":
        SDDC_OCID = arg

if SDDC_OCID =="":
    print ("No SDDC OCID Specified")
    sys.exit(2)

print ("Getting all ESXi hosts information")
esxi_hosts = esxi.list_esxi_hosts(sddc_id=SDDC_OCID).data.items

esxi_vnics = []

for esxi_host in sorted(esxi_hosts, key=operator.attrgetter('display_name')):
    print ("- {}".format(esxi_host.display_name))
    vnics_attachements = compute.list_vnic_attachments(compartment_id=esxi_host.compartment_id, instance_id=esxi_host.compute_instance_id).data
    vnics_attachements = sorted(vnics_attachements, key=operator.attrgetter('nic_index', 'vlan_tag'))

    for vnic in vnics_attachements:
        if vnic.vlan_id:
            vlan = network.get_vlan(vlan_id=vnic.vlan_id).data
            cidr = vlan.cidr_block
        else:
            cidr = ""
        print ("  - vnic {} - vlanID: {} - CIDR: {}".format(vnic.nic_index, vnic.vlan_tag, cidr))






