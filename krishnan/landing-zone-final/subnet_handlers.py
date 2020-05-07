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


# Match subnet name from list
def check_subnet_name_match(client, compartment_ocid, subnet_detail, vcn_ocid):
    is_match_found = False
    try:
        subnetsList = client.list_subnets(
            compartment_id=compartment_ocid,
            vcn_id=vcn_ocid,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        subnets = convert_response_to_dict(subnetsList)
        for subnet in subnets:
            if subnet["display_name"] == subnet_detail["name"]:
                is_match_found = True
        return is_match_found

    except Exception as inst:
        if inst.status and inst.message:
            error_handle("SUBNET", inst.status, inst.message)
        else:
            error_handle("SUBNET", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check if subnet is available lifecycle_state from subnet name
def check_subnet_availability(client, compartment_ocid, subnet_detail, vcn_ocid):
    is_match_found = False
    try:
        subnetsList = client.list_subnets(
            compartment_id=compartment_ocid,
            vcn_id=vcn_ocid,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        subnets = convert_response_to_dict(subnetsList)
        for subnet in subnets:
            if subnet["display_name"] == subnet_detail["name"]:
                if subnet["lifecycle_state"] == "AVAILABLE":
                    is_match_found = True
        return is_match_found

    except Exception as inst:
        if inst.status and inst.message:
            error_handle("SUBNET", inst.status, inst.message)
        else:
            error_handle("SUBNET", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check and return subnet ocid if available by name
def get_subnet_ocid_by_name(client, compartment_ocid, subnet_detail, vcn_ocid):
    matched_subnet_ocid = None
    try:
        subnetsList = client.list_subnets(
            compartment_id=compartment_ocid,
            vcn_id=vcn_ocid,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        subnets = convert_response_to_dict(subnetsList)
        for subnet in subnets:
            if subnet["display_name"] == subnet_detail["name"]:
                matched_subnet_ocid = subnet["id"]
        return matched_subnet_ocid

    except Exception as inst:
        if inst.status and inst.message:
            error_handle("SUBNET", inst.status, inst.message)
        else:
            error_handle("SUBNET", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Create Subnet
def create_subnet(client, compartment_ocid, subnet_detail, vcn_ocid):
    assign_public_ip = True if subnet_detail["is_public"] == "True" else False
    try:
        create_subnet_details = oci.core.models.CreateSubnetDetails(
            cidr_block=subnet_detail["cidr"], display_name=subnet_detail["name"],
            compartment_id=compartment_ocid,
            prohibit_public_ip_on_vnic=assign_public_ip,
            vcn_id=vcn_ocid)
        subnet_response = client.create_subnet(
            create_subnet_details=create_subnet_details,
        )
        subnet = convert_response_to_dict(subnet_response)
        print_decorator("SUBNET CREATED")
        return subnet["id"]

    except Exception as inst:
        if inst.status and inst.message:
            error_handle("SUBNET", inst.status, inst.message)
        else:
            error_handle("SUBNET", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


def check_create_subnet(client, subnet_details, vcn_ocid):
    matched_subnet_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], subnet_details["compartment_name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)

    if compartment_exist_check and compartment_available_check:
        vcn_exist = check_vcn_exist_by_ocid(client, compartment_ocid, vcn_ocid)
        vcn_available_state = check_vcn_ocid_is_available(
            client, compartment_ocid, vcn_ocid)

        if vcn_exist and vcn_available_state:
            subnet_name_match = check_subnet_name_match(
                client, compartment_ocid, subnet_details, vcn_ocid)
            if subnet_name_match:
                subnet_availability = check_subnet_availability(
                    client, compartment_ocid, subnet_details, vcn_ocid)
                if subnet_availability:
                    subnet_ocid = get_subnet_ocid_by_name(
                        client, compartment_ocid, subnet_details, vcn_ocid)
                    matched_subnet_ocid = subnet_ocid
                    print_decorator(
                        "SUBNET ALREADY EXISTS. SKIPPING SUBNET CREATION")
            if matched_subnet_ocid is None:
                matched_subnet_ocid = create_subnet(
                    client, compartment_ocid, subnet_details, vcn_ocid)
    return matched_subnet_ocid
