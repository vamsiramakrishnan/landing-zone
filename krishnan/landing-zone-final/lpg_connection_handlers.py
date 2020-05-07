import oci
from utils import convert_response_to_dict
from utils import extract_value_by_field
from utils import print_decorator
from utils import error_handle
from compartment_handlers import get_compartment_ocid_from_name
from compartment_handlers import check_if_compartment_exist
from compartment_handlers import check_if_compartment_is_active
from lpg_handlers import check_peering_status


# Read config and create clients (identity,network,etc.)
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)


# Connect Local Peering Gateway between Hub and Spokes VCN
def connect_local_peering_gateway(client, source_lpg_id, peer_lpg_id):
    try:
        connect_lpg_details = oci.core.models.ConnectLocalPeeringGatewaysDetails(
            peer_id=peer_lpg_id)
        connect_lpg = client.connect_local_peering_gateways(
            source_lpg_id, connect_local_peering_gateways_details=connect_lpg_details)
        print_decorator('LPG CONNECTED')
        return convert_response_to_dict(connect_lpg)
    except Exception as inst:
        if inst.status and inst.message:
            error_handle("LPG CONNECTION", inst.status, inst.message)
        else:
            error_handle("LPG CONNECTION", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check and create LPG connection
def check_connect_lpg(client, lpg, source_lpg_ocid, peer_lpg_ocid):
    if_source_lpg_peered = False
    if_target_lpg_peered = False

    peering_response = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], lpg["compartment_name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)

#     vcn_exist = check_vcn_exist_by_ocid(client, lpg["compartment_id"], source_vcn_ocid)
#     vcn_available_state = check_vcn_ocid_is_available(client, lpg["compartment_id"], source_vcn_ocid)

    if_source_lpg_peered = check_peering_status(client, source_lpg_ocid)
    if_target_lpg_peered = check_peering_status(client, peer_lpg_ocid)


#     if vcn_exist and vcn_available_state:
    if if_source_lpg_peered:
        print_decorator(
            "SOURCE LPG {} IS ALREADY PEERED".format(source_lpg_ocid))
        peering_response = None
    elif if_target_lpg_peered:
        print_decorator(
            "TARGET LPG {} IS ALREADY PEERED".format(peer_lpg_ocid))
        peering_response = None
    elif not if_source_lpg_peered and not if_target_lpg_peered:
        peering_response = connect_local_peering_gateway(
            client, source_lpg_ocid, peer_lpg_ocid)
    else:
        peering_response = None
    return peering_response
