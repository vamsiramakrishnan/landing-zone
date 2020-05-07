import oci
from utils import convert_response_to_dict
from utils import extract_value_by_field
from utils import print_decorator
from utils import error_handle
from compartment_handlers import get_compartment_ocid_from_name
from compartment_handlers import check_if_compartment_exist
from compartment_handlers import check_if_compartment_is_active
from vcn_handlers import check_vcn_exist_by_ocid
from vcn_handlers import check_vcn_ocid_is_available


# Read config and create clients (identity,network,etc.)
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)
virtual_network_client = oci.core.VirtualNetworkClient(config)


# Check if DHCP Options exists by name based on compartment ID and VCN ID
def check_if_dhcp_options_exists_by_name(client, compartment_id, vcn_ocid, dhcp_name):
    is_match_found = False
    try:
        listDhcpOptions = client.list_dhcp_options(compartment_id=compartment_id,
                                                   vcn_id=vcn_ocid,
                                                   retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,)
        DhcpOptions = convert_response_to_dict(listDhcpOptions)
        for dhcp in DhcpOptions:
            if dhcp["display_name"] == dhcp_name:
                is_match_found = True
            else:
                is_match_found = False
        return is_match_found

    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DHCP", inst.status, inst.message)
        else:
            error_handle("DHCP", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check if DHCP Options exists by name based on compartment ID and VCN ID and return dhcp OCID
def get_dhcp_ocid_by_name(client, compartment_id, vcn_ocid, dhcp_name):
    is_match_found_ocid = None
    try:
        listDhcpOptions = client.list_dhcp_options(compartment_id=compartment_id,
                                                   vcn_id=vcn_ocid,
                                                   retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,)
        DhcpOptions = convert_response_to_dict(listDhcpOptions)
        for dhcp in DhcpOptions:
            if dhcp["display_name"] == dhcp_name:
                is_match_found_ocid = dhcp["id"]
            else:
                is_match_found_ocid = None
        return is_match_found_ocid

    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DHCP", inst.status, inst.message)
        else:
            error_handle("DHCP", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check DHCP Options if exists by OCID based on compartment ID and VCN ID
def check_if_dhcp_options_exists_by_ocid(client, compartment_id, vcn_ocid, dhcp_ocid):
    is_match_found = False
    try:
        listDhcpOptions = client.list_dhcp_options(compartment_id=compartment_id,
                                                   vcn_id=vcn_ocid,
                                                   retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,)
        DhcpOptions = convert_response_to_dict(listDhcpOptions)
        for dhcp in DhcpOptions:
            if dhcp["id"] == dhcp_ocid:
                print(dhcp)
                is_match_found = True
            else:
                is_match_found = False
        return is_match_found

    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DHCP", inst.status, inst.message)
        else:
            error_handle("DHCP", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check DHCP Options if exists by name and state is available based on compartment ID and VCN ID
def check_if_dhcp_options_lifecycle_ocid(client, compartment_id, vcn_ocid, dhcp_ocid):
    is_match_found = False
    try:
        listDhcpOptions = client.list_dhcp_options(compartment_id=compartment_id,
                                                   vcn_id=vcn_ocid,
                                                   retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,)
        DhcpOptions = convert_response_to_dict(listDhcpOptions)
        for dhcp in DhcpOptions:
            if dhcp["lifecycle_state"] == "AVAILABLE":
                is_match_found = True
            else:
                is_match_found = False
        return is_match_found

    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DHCP", inst.status, inst.message)
        else:
            error_handle("DHCP", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Create DHCP
"""server_type can be "VcnLocal", "VcnLocalPlusInternet", "CustomDnsServer", "UNKNOWN_ENUM_VALUE"
type can be "DomainNameServer" or "SearchDomain"
"""


def create_dhcp(client, compartment_id, vcn_ocid, dhcp_options, dhcp_name):
    try:
        dhcpDetails = oci.core.models.CreateDhcpDetails(
            compartment_id=compartment_id, options=dhcp_options, vcn_id=vcn_ocid, display_name=dhcp_name)
        dhcpResponse = client.create_dhcp_options(
            create_dhcp_details=dhcpDetails)
        dhcpRes = convert_response_to_dict(dhcpResponse)
        return dhcpRes
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


def check_create_dhcp(client, compartment_name, vcn, vcn_ocid, dhcp):
    matched_dhcp_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], compartment_name)
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)

    vcn_exist = check_vcn_exist_by_ocid(client, compartment_ocid, vcn_ocid)
    vcn_available_state = check_vcn_ocid_is_available(
        client, compartment_ocid, vcn_ocid)

    dhcp_name_check = check_if_dhcp_options_exists_by_name(
        client, compartment_ocid, vcn_ocid, dhcp["name"])

    if compartment_exist_check and compartment_available_check:
        print_decorator(
            "COMPARTMENT EXIST AND IS IN AVAILABLE LIFECYCLE STATE")
        if vcn_exist and vcn_available_state and dhcp_name_check:
            matched_dhcp_ocid = get_dhcp_ocid_by_name(
                client, compartment_ocid, vcn_ocid, dhcp["name"])
            dhcp_available_state = check_if_dhcp_options_lifecycle_ocid(
                client, compartment_ocid, vcn_ocid, matched_dhcp_ocid)
            if matched_dhcp_ocid is not None and dhcp_available_state:
                print_decorator("DHCP ALREADY EXIST")
                return matched_dhcp_ocid
        elif matched_dhcp_ocid is None:
            matched_dhcp_ocid = create_dhcp(
                virtual_network_client, compartment_ocid, vcn_ocid, dhcp["options"], dhcp["name"])
    return matched_dhcp_ocid
