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


# Check if LPG name matches
def check_if_lpg_exist_by_name(client, compartment_ocid, vcn_ocid, lpg_name):
    if_match_found = False
    try:
        listLpgs = client.list_local_peering_gateways(
            compartment_id=compartment_ocid, vcn_id=vcn_ocid)
        lpgs = convert_response_to_dict(listLpgs)
        lpg_names = extract_value_by_field(lpgs, "display_name")
        if lpg_name in lpg_names:
            if_match_found = True
        else:
            if_match_found = False
        return if_match_found
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("LPG", inst.status, inst.message)
        else:
            error_handle("LPG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Get LPG OCID from matching name
def get_lpg_ocid_by_lpg_name(client, compartment_ocid, vcn_ocid, lpg_name):
    lpg_id = None
    try:
        listLpgs = client.list_local_peering_gateways(
            compartment_id=compartment_ocid, vcn_id=vcn_ocid)
        lpgs = convert_response_to_dict(listLpgs)
        for lpg in lpgs:
            if lpg["display_name"] == lpg_name:
                lpg_id = lpg["id"]
        return lpg_id
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("LPG", inst.status, inst.message)
        else:
            error_handle("LPG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check for LPG state
def check_if_lpg_is_available(client, lpg_ocid, compartment_ocid):
    is_match_found = False
    try:
        lpg = client.get_local_peering_gateway(
            local_peering_gateway_id=lpg_ocid)
        lpg_dict = convert_response_to_dict(lpg)
        if lpg_dict["lifecycle_state"] == "AVAILABLE":
            is_match_found = True
        else:
            is_match_found = False
        return is_match_found
    except Exception as inst:
        print(inst)
        exception = inst
        if inst.status and inst.message:
            error_handle("LPG", inst.status, inst.message)
        else:
            error_handle("LPG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check if connection is established
def check_peering_status(client, lpg_ocid):
    try:
        lpg = client.get_local_peering_gateway(local_peering_gateway_id=lpg_ocid,
                                               retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,)
        lpg_dict = convert_response_to_dict(lpg)
        if lpg_dict["peering_status"] == "PEERED":
            return True
        else:
            return False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("LPG", inst.status, inst.message)
        else:
            error_handle("LPG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Create Local Peering Gateway been Hub and Spokes VCN
def create_local_peering_gateway(composite_client, lpg_name, compartment_id, vcn_ocid):
    try:
        create_lpg_details = oci.core.models.CreateLocalPeeringGatewayDetails(
            compartment_id=compartment_id, display_name=lpg_name, vcn_id=vcn_ocid)
        create_lpg_response = composite_client.create_local_peering_gateway_and_wait_for_state(
            create_lpg_details,
            wait_for_states=[
                oci.core.models.LocalPeeringGateway.LIFECYCLE_STATE_AVAILABLE]
        )
        lpg = create_lpg_response
        lpg_dict = convert_response_to_dict(lpg)
        print_decorator("CREATED LPG")
        return lpg_dict["id"]

    except Exception as inst:
        if inst.status and inst.message:
            error_handle("LPG", inst.status, inst.message)
        else:
            error_handle("LPG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


def check_create_lpg(client, composite_client, vcn, lpg, vcn_ocid):
    matched_lpg_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], lpg["compartment_name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)

    vcn_exist = check_vcn_exist_by_ocid(client, compartment_ocid, vcn_ocid)
    vcn_available_state = check_vcn_ocid_is_available(
        client, compartment_ocid, vcn_ocid)

    lpg_name_check = check_if_lpg_exist_by_name(
        client, compartment_ocid, vcn_ocid, lpg["name"])

    if compartment_exist_check and compartment_available_check:
        print_decorator(
            "COMPARTMENT EXIST AND IS IN AVAILABLE LIFECYCLE STATE")
        if vcn_exist and vcn_available_state and lpg_name_check:
            matched_lpg_ocid = get_lpg_ocid_by_lpg_name(
                client, compartment_ocid, vcn_ocid, lpg["name"])
            lpg_available_state = check_if_lpg_is_available(
                client, matched_lpg_ocid, compartment_ocid)
            if matched_lpg_ocid is not None and lpg_available_state:
                print_decorator("LPG ALREADY EXIST")
                return matched_lpg_ocid
        elif matched_lpg_ocid is None:
            matched_lpg_ocid = create_local_peering_gateway(
                composite_client, lpg["name"], compartment_ocid, vcn_ocid)
    return matched_lpg_ocid
