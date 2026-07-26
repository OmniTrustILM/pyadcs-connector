from asn1crypto.core import Sequence, ObjectIdentifier, Integer


class CertificateTemplateOid(Sequence):
    _fields = [
        ('templateID', ObjectIdentifier),
        ('templateMajorVersion', Integer, {'optional': True}),
        ('templateMinorVersion', Integer, {'optional': True})
    ]
