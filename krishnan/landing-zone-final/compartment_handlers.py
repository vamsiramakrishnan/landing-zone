import oci
from utils import convert_response_to_dict
from utils import error_handle


# Check if compartment exists
def check_if_compartment_exist(client, compartment_ocid):
    try:
        compartmentResponse = client.get_compartment(
            compartment_id=compartment_ocid,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        compartment_detail = convert_response_to_dict(compartmentResponse)
        return True if compartment_detail["id"] == compartment_ocid else False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("COMPARTMENT", inst.status, inst.message)
        else:
            error_handle("COMPARTMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False


# Check if compartment is active
def check_if_compartment_is_active(client, compartment_ocid):
    try:
        compartment_response = client.get_compartment(
            compartment_id=compartment_ocid, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        compartment = convert_response_to_dict(compartment_response)
        return True if compartment["lifecycle_state"] == "ACTIVE" else False
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("COMPARTMENT", inst.status, inst.message)
        else:
            error_handle("COMPARTMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return False

# Fetch all compartments by tenancy


def fetch_all_compartments_in_tenancy(client, tenancy_ocid):
    try:
        """Fetch all Compartments in Tenancy , and look across all subtrees."""
        compartmentResponse = oci.pagination.list_call_get_all_results(
            client.list_compartments,
            compartment_id=tenancy_ocid,
            limit=200,
            access_level="ACCESSIBLE",
            compartment_id_in_subtree=True,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        return convert_response_to_dict(compartmentResponse)
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("COMPARTMENT", inst.status, inst.message)
        else:
            error_handle("COMPARTMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None

# Filter compartment by state = active


def filter_compartments_by_state(compartmentList=[], compartmentState="ACTIVE"):
    try:
        """Filter Compartments by their lifecycle state, ACTIVE| DELETNG | DELETED | CREATING"""
        filteredCompartments = [
            compartment
            for compartment in compartmentList
            if compartment["lifecycle_state"] == compartmentState
        ]
        return filteredCompartments
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("COMPARTMENT", inst.status, inst.message)
        else:
            error_handle("COMPARTMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None

# Get compartment OCID from name


def get_compartment_ocid_from_name(client, tenancy_ocid, compartment_name):
    compartment_ocid = None
    try:
        compartments = fetch_all_compartments_in_tenancy(client, tenancy_ocid)
        activeCompartments = filter_compartments_by_state(
            compartmentList=compartments, compartmentState="ACTIVE"
        )
        for compartment in activeCompartments:
            if compartment_name == compartment["name"]:
                compartment_ocid = compartment["id"]
        return compartment_ocid
    except Exception as inst:
        exception = inst
        if inst.status and inst.message:
            error_handle("COMPARTMENT", inst.status, inst.message)
        else:
            error_handle("COMPARTMENT", "UNKNOWN", "UNKNOWN ERROR MESSAGE")
        return None
