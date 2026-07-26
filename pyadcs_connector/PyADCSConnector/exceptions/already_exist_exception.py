class AlreadyExistException(Exception):
    def __init__(self, object_type, identifier):
        self.object_type = object_type
        self.identifier = identifier

    def __str__(self):
        return "Object of type " + self.object_type + " identified by " + self.identifier + " already exists."
