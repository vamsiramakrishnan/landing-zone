# All necessary imports here
import oci
import os
import logging
import pprint
import re
import ipaddr  # pip3 install ipaddr


# local logger
def local_logger(value):
    print(value)


def print_decorator(message):
    print("====================")
    print(message)
    print("====================")


def error_handle(resource, status, message):
    print("========{} ERROR============".format(resource))
    print("{} ERROR".format(status))
    print(message)
    print("====================")


# Helper methods for extracting and json_lookup
def extract_value_by_field(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results


# helper method to convert response to dictionary
def convert_response_to_dict(oci_response):
    return oci.util.to_dict(oci_response.data)


# Special Characters Regex validation
def special_char_regex_validation(value):
    special_chars_regex = re.compile(r'[@!#$%^&*()<>?/\|}{~:`]')
    special_char_check = special_chars_regex.search(value)
    if special_char_check is None:
        return True
    else:
        return False


# IPV4 CIDR Notation Regex Validation
def ipv4_regex_validation(value):
    ipv4_cidr_regex = re.compile(
        '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])/(1[0-9]|2[0-9]|3[0-1])$')
    ipv4_cidr_check = ipv4_cidr_regex.search(value)
    if ipv4_cidr_check is None:
        return False
    else:
        return True


# File exists
def file_exist_check(filePath):
    try:
        does_exist = os.path.exists(filePath)
        if does_exist:
            print_decorator(
                "FILE EXISTS IN DIRECTORY!\nPROCEEDING FOR SANITY CHECK !")
            return True
        else:
            print_decorator(
                "MISSING FILE.\nFILE DOES NOT EXIST IN DIRECTORY !")
            return False
    except Exception as inst:
        print_decorator(inst)
        return False


# Sanity check
def json_sanity_check(payload):
    completed = False
    all_names = []
    cidr_blocks = []

    hub = payload["hub"]
    spokes = payload["spokes"]
    spoke_vcn = []

    for spoke in spokes:
        spoke_vcn.append(spoke["vcn"])

    all_names.extend(extract_value_by_field(payload, "name"))
    all_names.extend(extract_value_by_field(payload, "dns_label"))

    cidr_blocks.extend(extract_value_by_field(hub, "cidr_block"))
    cidr_blocks.extend(extract_value_by_field(spoke_vcn, "cidr_block"))

    is_cidr_sanity_check = True
    is_cidr_overlap_check = False
    is_names_sanity_check = True

    for name in all_names:
        is_names_sanity_check = special_char_regex_validation(name)
        if not is_names_sanity_check:
            break

    for index_out, cidr_out in enumerate(cidr_blocks):
        is_cidr_sanity_check = ipv4_regex_validation(cidr_out)

        if not is_cidr_sanity_check:
            break

        for index_in, cidr_in in enumerate(cidr_blocks):
            if index_in != index_out:
                ip_range_out = ipaddr.IPNetwork(cidr_out)
                ip_range_in = ipaddr.IPNetwork(cidr_in)
                is_cidr_overlap_check = ip_range_out.overlaps(ip_range_in)
                if is_cidr_overlap_check:
                    break

    if not is_cidr_sanity_check:
        print_decorator("INVALID VCN CIDR BLOCKS.\nERROR IN CIDR BLOCK FOUND")
        completed = False

    if is_cidr_overlap_check:
        print_decorator(
            "INVALID VCN CIDR BLOCKS.\nCIDR BLOCKS ARE OVERLAPPING")
        completed = False

    if not is_names_sanity_check:
        print_decorator(
            "IMPROPER NAMING CONVENTION.\nSPECIAL CHARACTERS IN NAMES NOT ALLOWED")
        completed = False

    if is_cidr_sanity_check and not is_cidr_overlap_check and is_names_sanity_check:
        print_decorator(
            "FILE SANITY CHECK COMPLETED SUCCESSFULLY\nNO ERROR FOUND")
        completed = True
    return completed
