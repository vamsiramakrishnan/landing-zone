import oci
from utils import convert_response_to_dict
from utils import extract_value_by_field
from utils import print_decorator
from utils import error_handle
from compartment_handlers import get_compartment_ocid_from_name
from compartment_handlers import check_if_compartment_exist
from compartment_handlers import check_if_compartment_is_active


# Read config and create clients (identity,network,etc.)
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)


# Check if DRG exist by name
def check_if_drg_exist_by_name(client, compartment_ocid, drg_name):
    try:
        listDRGs = client.list_drgs(compartment_id=compartment_ocid)
        drgs = convert_response_to_dict(listDRGs)
        drg_name_extract = extract_value_by_field(drgs, "display_name")
        return True if drg_name in drg_name_extract else False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG", inst.status, inst.message)
        else:
            error_handle("DRG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check if DRG exist already by OCID and State in Compartment
def check_drg_ocid_is_available(client, compartment_ocid, drg_ocid):
    try:
        drg = client.get_drg(
            drg_id=drg_ocid, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        drg_dict = convert_response_to_dict(drg)
        if drg_dict is not None and drg_dict["lifecycle_state"] == "AVAILABLE":
            return True
        else:
            return False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG", inst.status, inst.message)
        else:
            error_handle("DRG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Get DRG OCID from DRG Name
def get_drg_match_ocid(client, compartment_ocid, drg_name):
    try:
        listDRGs = client.list_drgs(compartment_id=compartment_ocid)
        drgs = convert_response_to_dict(listDRGs)
        for drg in drgs:
            if drg["display_name"] == drg_name:
                return drg["id"]
            else:
                return None
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG", inst.status, inst.message)
        else:
            error_handle("DRG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Create DRG
def create_drg(client, drg):
    try:
        compartment_ocid = get_compartment_ocid_from_name(
            identity_client, config["tenancy"], drg["compartment_name"])
        drg_result = client.create_drg(
            oci.core.models.CreateDrgDetails(
                compartment_id=compartment_ocid,
                display_name=drg["name"]
            )
        )
        drg = oci.wait_until(
            client,
            client.get_drg(drg_result.data.id),
            'lifecycle_state',
            'AVAILABLE'
        )
        print_decorator("CREATING DRG")
        drg_new = convert_response_to_dict(drg)
        return drg_new["id"]
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG", inst.status, inst.message)
        else:
            error_handle("DRG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check and create DRG if doesn't exist
def check_create_drg(client, drg):
    matched_drg_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], drg["compartment_name"])
    drg_name_check = check_if_drg_exist_by_name(
        client, compartment_ocid, drg["name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)
    if compartment_exist_check and compartment_available_check:
        print_decorator(
            "COMPARTMENT EXIST AND IS IN AVAILABLE LIFECYCLE STATE")
        if drg_name_check:
            matched_drg_ocid = get_drg_match_ocid(
                client, compartment_ocid, drg["name"])
            drg_available_state = check_drg_ocid_is_available(
                client, compartment_ocid, matched_drg_ocid)
            if matched_drg_ocid is not None and drg_available_state:
                print_decorator("DRG ALREADY EXIST")
                return matched_drg_ocid
        elif matched_drg_ocid is None:
            matched_drg_ocid = create_drg(client, drg)
    return matched_drg_ocid
