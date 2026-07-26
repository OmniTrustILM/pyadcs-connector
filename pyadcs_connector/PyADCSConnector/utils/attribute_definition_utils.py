def get_attribute_value(attribute_name, attributes):
    for attribute in attributes:
        if attribute.get("name") == attribute_name:
            contents = attribute.get("content", {})
            if contents and len(contents) > 0:
                return contents[0].get("data")

    return ""


def get_attribute_value_list(attribute_name, attributes):
    for attribute in attributes:
        if attribute.get("name") == attribute_name:
            contents = attribute.get("content", {})
            if contents and len(contents) > 0:
                return [val.get("data") for val in contents]

    return []


def set_attribute_value(attribute_name, attributes, value):
    for attribute in attributes:
        if attribute.get("name") == attribute_name:
            attribute.set("content", [value])
            return True
    return False


def get_attribute_content(attribute_name, attributes):
    for attribute in attributes:
        if attribute.get("name") == attribute_name:
            return attribute.get("content", {})
    return ""


def merge_attributes(request_attributes, original_attributes):
    merged_attributes = list()
    print(request_attributes)
    request_attributes_by_uuid = {val["name"]: val for val in request_attributes}
    for i in original_attributes:
        if i["name"] in request_attributes_by_uuid.keys():
            corresponding_request_attribute = request_attributes_by_uuid.get(i["name"])
            i["content"] = corresponding_request_attribute["content"]
            merged_attributes.append(i)
    return merged_attributes
