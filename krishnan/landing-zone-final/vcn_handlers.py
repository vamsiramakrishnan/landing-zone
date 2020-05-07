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


# Check if existing VCN matches by Name
def check_vcn_name_match(client, compartment_id, vcn_name):
    try:
        listVCNReponse = client.list_vcns(compartment_id=compartment_id)
        vcns = convert_response_to_dict(listVCNReponse)
        vcn_names = extract_value_by_field(vcns, "display_name")
        if vcn_name in vcn_names:
            print_decorator("VCN NAME ALREADY EXIST. SKIPPING VCN CREATION")
            return True
        else:
            print_decorator(
                "NO VCN NAME MATCH FOUND. VCN CIDR CHECK IN PROGRESS...")
            return False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Check if existing VCN matches by CIDR
def check_vcn_cidr_match(client, compartment_id, vcn_cidr_block):
    is_match_found = False
    try:
        getResponse = client.list_vcns(compartment_id=compartment_id)
        vcns = convert_response_to_dict(getResponse)
        for vcn in vcns:
            vcn_cidr_ip = vcn["cidr_block"].split("/")[0]
            input_cidr_ip = vcn_cidr_block.split("/")[0]
            if vcn["cidr_block"] == vcn_cidr_block or vcn_cidr_ip == input_cidr_ip:
                is_match_found = True
                break
            else:
                is_match_found = False
        if is_match_found:
            print_decorator("VCN CIDR ALREADY EXIST. SKIPPING VCN CREATION")
        else:
            print_decorator("NO VCN CIDR MATCH FOUND.")
        return is_match_found
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Check if VCN exist from OCID
def check_vcn_exist_by_ocid(client, compartment_id, vcn_ocid):
    try:
        vcnResponse = client.get_vcn(vcn_id=vcn_ocid)
        vcn = convert_response_to_dict(vcnResponse)
        return True if vcn["id"] == vcn_ocid else False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Check if VCN is is AVAILABLE STATE
def check_vcn_ocid_is_available(client, compartment_id, vcn_ocid):
    try:
        vcnResponse = client.get_vcn(vcn_id=vcn_ocid)
        vcn = convert_response_to_dict(vcnResponse)
        return True if vcn["lifecycle_state"] == "AVAILABLE" else False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Get VCN OCID from Name or CIDR
def get_vcn_match_ocid(client, compartment_id, vcn_name=None, vcn_cidr=None):
    try:
        listVCNReponse = client.list_vcns(compartment_id=compartment_id)
        vcns = convert_response_to_dict(listVCNReponse)
        vcn_ocid = None
        for vcn in vcns:
            if vcn_name is not None:
                if vcn["display_name"] == vcn_name:
                    vcn_ocid = vcn["id"]
            elif vcn_cidr is not None:
                if vcn["cidr_block"] == vcn_cidr:
                    vcn_ocid = vcn["id"]
        return vcn_ocid
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Create VCN
def create_vcn(client, composite_client, vcn):
    try:
        compartment_ocid = get_compartment_ocid_from_name(
            identity_client, config["tenancy"], vcn["compartment_name"])
        vcn_details = oci.core.models.CreateVcnDetails(cidr_block=vcn["cidr_block"],
                                                       display_name=vcn["name"],
                                                       compartment_id=compartment_ocid,
                                                       dns_label=vcn["dns_label"])
        VCNResponse = composite_client.create_vcn_and_wait_for_state(
            vcn_details,
            wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_AVAILABLE]
        )
        vcn = convert_response_to_dict(VCNResponse)
        print_decorator("CREATING VCN")
        return vcn["id"]
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("VCN", inst.status, inst.message)
        else:
            error_handle("VCN", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check and create VCN
def check_create_vcn(client, composite_client, vcn):
    matched_vcn_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], vcn["compartment_name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)
    if compartment_exist_check and compartment_available_check:
        print_decorator(
            "COMPARTMENT EXIST AND IS IN AVAILABLE LIFECYCLE STATE")
        vcn_name_check = check_vcn_name_match(
            client, compartment_ocid, vcn["name"])
        vcn_cidr_check = check_vcn_cidr_match(
            client, compartment_ocid, vcn["cidr_block"])
        if vcn_name_check:
            matched_vcn_ocid = get_vcn_match_ocid(
                client, compartment_ocid, vcn["name"])
        if vcn_cidr_check:
            matched_vcn_ocid = get_vcn_match_ocid(
                client, compartment_ocid, vcn_cidr=vcn["cidr_block"])
    if matched_vcn_ocid is not None:
        vcn_available_check = check_vcn_ocid_is_available(
            client, compartment_ocid, matched_vcn_ocid)
        if vcn_available_check:
            return matched_vcn_ocid
    elif matched_vcn_ocid is None:
        return create_vcn(client, composite_client, vcn)
