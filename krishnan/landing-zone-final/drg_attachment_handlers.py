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
from drg_handlers import check_if_drg_exist_by_name
from drg_handlers import get_drg_match_ocid
from drg_handlers import check_drg_ocid_is_available


# Read config and create clients (identity,network,etc.)
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)
virtual_network_client = oci.core.VirtualNetworkClient(config)


# Check DRG attachment status
def get_drg_attachment_status(client, drg_attachment_ocid):
    try:
        drg_attachment = client.get_drg_attachment(
            drg_attachment_id=drg_attachment_ocid)
        drg_attachment_dict = convert_response_to_dict(drg_attachment)
        if drg_attachment_dict is not None and drg_attachment_dict["lifecycle_state"] == "ATTACHED":
            return True
        else:
            return False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG ATTACHMENT", inst.status, inst.message)
        else:
            error_handle("DRG ATTACHMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Get DRG attachment ocid from DRG OCID
def filter_drg_attachment_id(client, compartment_ocid, drg_id):
    try:
        drg_attachment_id = None
        drg_attachments = client.list_drg_attachments(
            compartment_id=compartment_ocid)
        drg_attachments_dict = convert_response_to_dict(drg_attachments)
        for drg_attachment in drg_attachments_dict:
            if drg_attachment["drg_id"] == drg_id:
                drg_attachment_id = drg_attachment["id"]
            else:
                drg_attachment_id = None
        return drg_attachment_id
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG ATTACHMENT", inst.status, inst.message)
        else:
            error_handle("DRG ATTACHMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Attach newly created DRG to VCN using VCN OCID
def drg_attach(client, vcn_ocid, drg_ocid, drg_name):
    try:
        drg_attach_result = client.create_drg_attachment(
            oci.core.models.CreateDrgAttachmentDetails(
                display_name=drg_name,
                vcn_id=vcn_ocid,
                drg_id=drg_ocid
            )
        )
        drg_attachment = oci.wait_until(
            client,
            client.get_drg_attachment(drg_attach_result.data.id),
            'lifecycle_state',
            'ATTACHED'
        )
        print_decorator('CREATED DRG ATTACHMENT')
        drg_attach = convert_response_to_dict(drg_attachment)
        return drg_attach["id"]
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("DRG", inst.status, inst.message)
        else:
            error_handle("DRG", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None


# Check and create DRG if doesn't exist
def check_create_drg_attachment(client, drg, vcn, drg_ocid, vcn_ocid):
    matched_drg_attachment_ocid = None
    compartment_ocid = get_compartment_ocid_from_name(
        identity_client, config["tenancy"], drg["compartment_name"])
    compartment_exist_check = check_if_compartment_exist(
        identity_client, compartment_ocid)
    compartment_available_check = check_if_compartment_is_active(
        identity_client, compartment_ocid)

    vcn_exist = check_vcn_exist_by_ocid(client, compartment_ocid, vcn_ocid)
    vcn_available_state = check_vcn_ocid_is_available(
        client, compartment_ocid, vcn_ocid)

    drg_name_check = check_if_drg_exist_by_name(
        client, compartment_ocid, drg["name"])
    if compartment_exist_check and compartment_available_check:
        print_decorator(
            "COMPARTMENT EXIST AND IS IN AVAILABLE LIFECYCLE STATE")
        if vcn_exist and vcn_available_state and drg_name_check:
            drg_ocid = get_drg_match_ocid(
                client, compartment_ocid, drg["name"])
            drg_available_state = check_drg_ocid_is_available(
                client, compartment_ocid, drg_ocid)
            if drg_ocid is not None and drg_available_state:
                drg_attachment_ocid = filter_drg_attachment_id(
                    client, compartment_ocid, drg_ocid)
                if drg_attachment_ocid is not None:
                    drg_attached_state = get_drg_attachment_status(
                        client, drg_attachment_ocid)
                    if drg_attachment_ocid is not None and drg_attached_state:
                        matched_drg_attachment_ocid = drg_attachment_ocid
                        print_decorator("DRG ALREADY ATTACHED TO EXISTING VCN")
                        return matched_drg_attachment_ocid
                elif matched_drg_attachment_ocid is None:
                    matched_drg_attachment_ocid = drg_attach(
                        client, vcn_ocid, drg_ocid, drg["name"])
    return matched_drg_attachment_ocid
