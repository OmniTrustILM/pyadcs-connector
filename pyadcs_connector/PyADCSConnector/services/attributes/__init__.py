"""
Script contains the constants for the attributes used int the project
"""
# Property Name of the attributes

NAME_ATTRIBUTE_PROPERTY = "name"
UUID_ATTRIBUTE_PROPERTY = "uuid"
TYPE_ATTRIBUTE_PROPERTY = "type"
CONTENT_TYPE_ATTRIBUTE_PROPERTY = "contentType"
LABEL_ATTRIBUTE_PROPERTY = "label"
DESCRIPTION_ATTRIBUTE_PROPERTY = "description"
READ_ONLY_ATTRIBUTE_PROPERTY = "readOnly"
REQUIRED_ATTRIBUTE_PROPERTY = "required"
VISIBLE_ATTRIBUTE_PROPERTY = "visible"
MUTLISELECT_ATTRIBUTE_PROPERTY = "multiSelect"
GROUP_ATTRIBUTE_PROPERTY = "group"
GLOBAL_ATTRIBUTE_PROPERTY = "global"
LIST_ATTRIBUTE_PROPERTY = "list"
CONTENT_ATTRIBUTE_PROPERTY = "content"
PROPERTIES_ATTRIBUTE_PROPERTY = "properties"
PROPERTY_ATTRIBUTE_CALLBACK = "attributeCallback"
CONSTRAINTS_ATTRIBUTE_PROPERTY = "constraints"

################################################################
# helper attribute functions
################################################################


def build_attribute(name: str, uuid: str, attribute_type: str, content_type: str or None, description: str,
                    properties: dict or None, content: list[dict] or None, callback: dict or None,
                    constraints: list[dict] or None):
    attribute = dict()
    attribute[NAME_ATTRIBUTE_PROPERTY] = name
    attribute[UUID_ATTRIBUTE_PROPERTY] = uuid
    attribute[TYPE_ATTRIBUTE_PROPERTY] = attribute_type
    attribute[CONTENT_TYPE_ATTRIBUTE_PROPERTY] = content_type
    attribute[DESCRIPTION_ATTRIBUTE_PROPERTY] = description
    attribute[PROPERTIES_ATTRIBUTE_PROPERTY] = properties
    attribute[CONTENT_ATTRIBUTE_PROPERTY] = content
    attribute[PROPERTY_ATTRIBUTE_CALLBACK] = callback
    attribute[CONSTRAINTS_ATTRIBUTE_PROPERTY] = constraints

    return attribute


def get_data_attribute_properties(
        label,
        is_read_only=False,
        is_required=True,
        is_list=False,
        is_visible=True,
        is_multi_select=False):
    attribute_properties = dict()
    attribute_properties[LABEL_ATTRIBUTE_PROPERTY] = label
    attribute_properties[READ_ONLY_ATTRIBUTE_PROPERTY] = is_read_only
    attribute_properties[REQUIRED_ATTRIBUTE_PROPERTY] = is_required
    attribute_properties[LIST_ATTRIBUTE_PROPERTY] = is_list
    attribute_properties[VISIBLE_ATTRIBUTE_PROPERTY] = is_visible
    attribute_properties[MUTLISELECT_ATTRIBUTE_PROPERTY] = is_multi_select

    return attribute_properties


def get_info_attribute_properties(
        label,
        is_visible=True,
        group=None):
    attribute_properties = dict()
    attribute_properties[LABEL_ATTRIBUTE_PROPERTY] = label
    attribute_properties[VISIBLE_ATTRIBUTE_PROPERTY] = is_visible
    attribute_properties[GROUP_ATTRIBUTE_PROPERTY] = group

    return attribute_properties


def get_metadata_attribute_properties(
        label,
        is_visible=True,
        group=None,
        is_global=False):
    attribute_properties = dict()
    attribute_properties[LABEL_ATTRIBUTE_PROPERTY] = label
    attribute_properties[VISIBLE_ATTRIBUTE_PROPERTY] = is_visible
    attribute_properties[GROUP_ATTRIBUTE_PROPERTY] = group
    attribute_properties[GLOBAL_ATTRIBUTE_PROPERTY] = is_global

    return attribute_properties
