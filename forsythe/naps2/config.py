import os
import xml.etree.ElementTree as ET
from contextlib import contextmanager

from forsythe.naps2.paths import get_naps2_config_path


def _parse_profiles_xml():
    profiles_xml_path = os.path.join(get_naps2_config_path(), 'profiles.xml')
    with open(profiles_xml_path) as fp:
        tree = ET.parse(fp)
    root = tree.getroot()
    assert root.tag == 'ArrayOfScanProfile'
    return root


def _list_device_ids_and_names():
    device_names_by_id = {}
    for profile in _parse_profiles_xml():
        device_elem = profile.find('Device')
        assert device_elem is not None
        id_elem, name_elem = device_elem.find('ID'), device_elem.find('Name')
        assert id_elem is not None and name_elem is not None
        device_names_by_id[id_elem.text] = name_elem.text
    return sorted(device_names_by_id.items(), key=lambda x: x[1])


def list_naps2_profile_names():
    profile_names = set()
    for profile in _parse_profiles_xml():
        name_elem = profile.find('DisplayName')
        assert name_elem is not None
        profile_names.add(name_elem.text)
    return sorted(profile_names)
