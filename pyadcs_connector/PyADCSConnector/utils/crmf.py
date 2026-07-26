from asn1crypto.algos import DigestAlgorithm
from asn1crypto.cms import EnvelopedData
from asn1crypto.core import Sequence, SequenceOf, Choice, Null, BitString, Integer, ObjectIdentifier, Any, \
    OctetBitString
from asn1crypto.csr import Version, CertificationRequestInfo
from asn1crypto.x509 import GeneralName, AlgorithmIdentifier, Name, Extensions, Time, PublicKeyInfo

"""ASN.1 type classes for Certificate Request Message Format, as specified by RFC 4211."""


class AttributeTypeAndValue(Sequence):
    _fields = [('type', ObjectIdentifier),
               ('value ', Any)]


class OptionalValidity(Sequence):
    _fields = [('notBefore', Time, {'optional': True, 'implicit': 0}),
               ('notAfter', Time, {'optional': True, 'implicit': 1})
               ]


class CertTemplate(Sequence):
    _fields = [('version', Version, {'optional': True, 'implicit': 0}),
               ('serialNumber', Integer, {'optional': True, 'implicit': 1}),
               ('signingAlg', AlgorithmIdentifier, {'optional': True, 'implicit': 2}),
               ('issuer', Name, {'optional': True, 'implicit': 3}),
               ('validity', OptionalValidity, {'optional': True, 'implicit': 4}),
               ('subject', Name, {'optional': True, 'explicit': 5}),
               ('publicKey', PublicKeyInfo, {'optional': True, 'implicit': 6}),
               ('issuerUID', BitString, {'optional': True, 'implicit': 7}),
               ('subjectUID', BitString, {'optional': True, 'implicit': 8}),
               ('extensions', Extensions, {'optional': True, 'implicit': 9})
               ]


class Controls(SequenceOf):
    _child_spec = AttributeTypeAndValue


class CertRequest(Sequence):
    _fields = [
        ('certReqId', Integer),
        ('certTemplate', CertTemplate),
        ('controls', Controls, {'optional': True})
    ]


class PKMACValue(Sequence):
    _fields = [('algId', AlgorithmIdentifier),
               ('value', BitString)]


class SubsequentMessage(Integer):
    _map = {0: 'encrCert', 1: 'challengeResp'}


class POPOPrivKey(Choice):
    _alternatives = [('thisMessage', BitString, {'implicit': 0}),
                     ('subsequentMessage', SubsequentMessage, {'implicit': 1}),
                     ('dhMAC', BitString, {'implicit': 2}),
                     ('agreeMAC', PKMACValue, {'implicit': 3}),
                     ('encryptedKey', EnvelopedData, {'implicit': 4})]


class AuthInfo(Choice):
    _alternatives = [('sender', GeneralName, {'implicit': 0}),
                     ('publicKeyMAC', PKMACValue)]


class POPOSigningKeyInput(Sequence):
    _fields = [
        ('authInfo', AuthInfo),
        ('publicKey', PublicKeyInfo)
    ]


class POPOSigningKey(Sequence):
    _fields = [('poposkInput', POPOSigningKeyInput, {'optional': True, 'implicit': 0}),
               ('algorithmIdentifier', AlgorithmIdentifier),
               ('signature', BitString)
               ]


class ProofOfPossession(Choice):
    _alternatives = [
        ('raVerified', Null, {'implicit': 0}),
        ('signature', POPOSigningKey, {'implicit': 1}),
        ('keyEncipherment', POPOPrivKey, {'implicit': 2}),
        ('keyAgreement', POPOPrivKey, {'implicit': 3})
    ]


class CertReqMsg(Sequence):
    _fields = [('certReq', CertRequest),
               ('popo', ProofOfPossession, {'optional': True}),
               ('regInfo', AttributeTypeAndValue, {'optional': True})
               ]


class CertReqMessages(SequenceOf):
    _child_spec = CertReqMsg


# Class allowing to pass digest algorithm as signature_algorithm in Certification Request
class CertificationRequestNullSigned(Sequence):
    _fields = [
        ('certification_request_info', CertificationRequestInfo),
        ('signature_algorithm', DigestAlgorithm),
        ('signature', OctetBitString),
    ]
