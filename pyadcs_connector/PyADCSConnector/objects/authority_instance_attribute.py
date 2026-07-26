class AuthorityInstanceAttribute:
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid

    @staticmethod
    def from_dict(authority_instance_dict):
        return AuthorityInstanceAttribute(
            authority_instance_dict["name"],
            authority_instance_dict["uuid"])

    @staticmethod
    def from_dicts(authority_instance_dicts):
        return [AuthorityInstanceAttribute.from_dict(authority_instance_dict)
                for authority_instance_dict in authority_instance_dicts]
