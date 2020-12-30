import oci
import sys, getopt
import time

#Location of config file
configfile = "~/.oci/config"

config = oci.config.from_file(configfile)
compute = oci.core.ComputeClient(config)
esxi = oci.ocvp.EsxiHostClient(config)
network = oci.core.VirtualNetworkClient(config)
sddc = oci.ocvp.SddcClient(config)

SDDC_OCID = ""
vlan_file = ""
vcn_id = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:f:v:", [""])
except getopt.GetoptError:
    print ("create-vlans.py -s <SDDC OCID> -f <vlan file>")
    sys.exit(2)

for opt, arg in opts:
    if opt == "-s":
        SDDC_OCID = arg
    if opt == "-f":
        vlan_file = arg

if SDDC_OCID =="":
    print ("No SDDC OCID Specified")
    sys.exit(2)

if vlan_file =="":
    print ("No vlan file Specified")
    sys.exit(2)


vlans = []

file = open(vlan_file, "r")
lines = file.readlines()
try:
    for line in lines:
        vnic, vlan, cidr = line.rstrip().split(",")
        vlans.append([vnic, vlan, cidr])
except:
    print ("Error reading vlan file")

sddc_info = sddc.get_sddc(sddc_id=SDDC_OCID).data


print ("Getting SDDC information...")
esxi_hosts = esxi.list_esxi_hosts(sddc_id=SDDC_OCID).data.items

vnics_attachements = compute.list_vnic_attachments(compartment_id=esxi_hosts[0].compartment_id, instance_id=esxi_hosts[0].compute_instance_id).data
for vnic_attachment in vnics_attachements:
    if vnic_attachment.vlan_tag == 0:
        subnet = network.get_subnet(subnet_id=vnic_attachment.subnet_id).data
        break

print ("Create VLAN for SDDC: {} in {}" .format(sddc_info.display_name, sddc_info.compute_availability_domain))
for vlan in vlans:
    print ("vnic: {}  -  vlan id: {}  -  cidr: {}".format(vlan[0], vlan[1], vlan[2]))

confirm = input ("\ntype yes to create and attach vlans: ")

if confirm == "yes":
    for vlan in vlans:
        vlandetails = oci.core.models.CreateVlanDetails()
        vlandetails.availability_domain = sddc_info.compute_availability_domain
        vlandetails.cidr_block = vlan[2]
        vlandetails.compartment_id = sddc_info.compartment_id
        vlandetails.vcn_id = subnet.vcn_id
        vlandetails.vlan_tag = int(vlan[1])
        vlandetails.display_name = "VLAN-{}".format(vlan[1])
        try:
            response = network.create_vlan(create_vlan_details=vlandetails)
        except oci.exceptions.ServiceError as response:
            print ("error creating vlan {} - {}".format(vlan[1], response.message))
            exit(1)
        new_vlan_id = response.data.id
        print ("Created vlan {}".format(vlan[1]))
        for esxi_host in esxi_hosts:
            vnicdetails = oci.core.models.CreateVnicDetails()
            vnicattachdetails = oci.core.models.AttachVnicDetails()
            vnicdetails.vlan_id = new_vlan_id
            vnicdetails.display_name = "VLAN-{}".format(vlan[1])
            vnicattachdetails.create_vnic_details = vnicdetails
            vnicattachdetails.display_name = "VLAN-{}".format(vlan[1])
            vnicattachdetails.nic_index = int(vlan[0])
            vnicattachdetails.instance_id = esxi_host.compute_instance_id
            doattach = True
            while doattach:
                try:
                    response = compute.attach_vnic(attach_vnic_details=vnicattachdetails)
                    if response.status == 200:
                        doattach = False
                except oci.exceptions.ServiceError as response:
                    if response.status == 409:
                        print ("waiting for instance modification to be completed...")
                        time.sleep(5)
                    else:
                        print("error attaching vnic to host {} - {} - {}".format(esxi_host.display_name, response.status, response.message))
                        exit(1)
                print (" - attached to ESXI host: {}".format(esxi_host.display_name))

print ("done")








