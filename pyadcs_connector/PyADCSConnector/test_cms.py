import base64

from asn1crypto import x509, keys, csr, cms
from asn1crypto.cms import ContentInfo
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase

from PyADCSConnector.utils import crmf, cmc
from PyADCSConnector.utils.adcs_asn1 import CertificateTemplateOid
from PyADCSConnector.utils.cmc import PKIData
from PyADCSConnector.utils.cms_utils import create_cms
from PyADCSConnector.utils.dump_parser import TemplateData


def _make_spki(pubkey) -> keys.PublicKeyInfo:
    spki_der = pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return keys.PublicKeyInfo.load(spki_der)


def _build_crmf_with_san(subject_cn: str, dns_names) -> str:
    """
    Build a CRMF CertReqMessages with:
      - subject = CN=subject_cn
      - publicKey = SPKI from a fresh RSA key
      - extensions = [ subjectAltName: dns_names ]
    Return: base64-encoded DER of CertReqMessages
    """
    # Subject: CN=...
    subject = x509.Name.build({"common_name": subject_cn})

    # Keypair -> SPKI
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    spki = _make_spki(key.public_key())

    # SAN extension
    gns = x509.GeneralNames([x509.GeneralName("dns_name", d) for d in dns_names])
    san_ext = x509.Extension({
        "extn_id": "subject_alt_name",    # 2.5.29.17
        "critical": False,
        "extn_value": gns,                # asn1crypto will wrap to OCTET STRING(der(GeneralNames))
    })
    exts = x509.Extensions([san_ext])

    # CertTemplate (asn1crypto.crmf uses camelCase names as in RFC 4211)
    tmpl = crmf.CertTemplate({
        "subject": subject,
        "publicKey": spki,
        "extensions": exts,
    })

    # CertRequest
    creq = crmf.CertRequest({
        "certReqId": 0,
        "certTemplate": tmpl,
    })

    # CertReqMsg -> CertReqMessages
    crm = crmf.CertReqMsg({"certReq": creq})
    crmf_msgs = crmf.CertReqMessages([crm])

    return base64.b64encode(crmf_msgs.dump()).decode("ascii")


class CmsTest(TestCase):

    def test_cms_util(self):
        crmf_encoded = "MIIDHTCCAxkwggH9AgEAMIIB9qNmMGQxDzANBgNVBAoMBnRvY2VjejEmMCQGA1UEAwwdZGV2ZWxvcC5sb2NhbGhvc3QubG9jYWxkb21haW4xKTAnBgkqhkiG9w0BCQEWGnJvb3RAbG9jYWxob3N0LmxvY2FsZG9tYWlupWYwZDEPMA0GA1UECgwGdG9jZWN6MSYwJAYDVQQDDB1kZXZlbG9wLmxvY2FsaG9zdC5sb2NhbGRvbWFpbjEpMCcGCSqGSIb3DQEJARYacm9vdEBsb2NhbGhvc3QubG9jYWxkb21haW6mggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDIrii/N6zI35rtw6sYmApohhNqOXRa8ktsqDPROdzdNc55aBVyTQFvf0z1XRi26l4GhsUv3KpLVTLV3vrCXtOTAeZccQgNqfKqDIVByjzWxGxFMuiTwpToB+a/CqXblaavTlyrv9varnxBEDjXK7H5iA4U+HxhM+WWidcSstnqGG8CnTmWS9cnj163zF01JzQANuIXKQ1CvJkHaMidbj5n5+w/nU/73BZEhnKivbOw3WWgVlV7fnR325FCF25J4AzJ2YyXo0Xu95cH0psjX0DM/ZroV+geiPZgGUp8cszkNYJMg5vHXSIQnYDDhDyiACy0QUqpxmK2iZdAqpTeI2W7AgMBAAGhggEUMA0GCSqGSIb3DQEBCwUAA4IBAQAeIxAUbjTOqCwl1egb7+Sr2U9kA65+tgydM5zYmc1qcOBFAo+ngMAD8WaG3hJRZgjGQP/HYxmx7lJAYU6RwvgD+c0bOHuB7kawFL1oyv0zhOVUnKmLrERVTjq1PYNYaEt3dfsrhGy1aziyyH4K4nOmBwINzJmy0wuPI8MeCbBTlu4V3hdmo8OpruCHxN2CgsxyrMwcPLUXQFy3lMhx3Mfc3ht7u8eFcaKLbraxmDDwtZbtoEcBTZFFrKoFkJERXZGiVRNkuk/vIc/ZpRvwg1y5CvbPCgj3CRbwrwOfXSWRYG7R7SJDMJTfOlAPt7GksF/kQr7aakQcsf9wBQ4K1HjE"
        ca_name = 'Authority'
        template_v1 = TemplateData('WebServer', 'temp_displ', '1', '1', '1.2.3')
        cms_v1 = create_cms(crmf_encoded, ca_name, template_v1)
        cms_object = ContentInfo.load(base64.b64decode(cms_v1))
        pki_data = PKIData.load(cms_object['content']['encap_content_info']['content'].native)
        cert_request = pki_data['reqSequence'][0].chosen['certificationRequest']

        # Check if hash value of the Certificate Request Info has expected value
        self.assertEqual(base64.b64encode(cert_request['signature'].native), b'AOlSQLNom8Jl3L0MxuBZgvcHYBhj7zHIr5A36kudDI4=')

        # Check if Certificate Template extension has correct value
        extension = cert_request['certification_request_info']['attributes'][0]['values'][0][0]
        self.assertEqual(extension['extn_value'].native, template_v1.name)

        # Check if Signer Info has correctly set SID issuer name
        signer_info = cms_object['content']['signer_infos'][0]
        self.assertEqual(signer_info['sid'].chosen['issuer'].native['common_name'], ca_name)

        # Check if Signer Info has expected signature value of Encapsulated Content Info content
        self.assertEqual(base64.b64encode(signer_info['signature'].native), b'+jCEBGh5z8VMhdb0yTX+AjFUuwE7YCh7YxkDE6Wze2M=')

        template_v2 = TemplateData('WebServer', 'temp_displ', '2', '2.4', '1.2.3')

        cms_v2 = create_cms(crmf_encoded, ca_name, template_v2)

        # Check if Certificate Template OID has been set correctly
        cms_object = ContentInfo.load(base64.b64decode(cms_v2))
        pki_data = PKIData.load(cms_object['content']['encap_content_info']['content'].native)
        cert_request = pki_data['reqSequence'][0].chosen['certificationRequest']
        extension = cert_request['certification_request_info']['attributes'][0]['values'][0][0]
        cert_template_oid = CertificateTemplateOid.load(extension['extn_value'].native)
        self.assertEqual(cert_template_oid['templateID'].native, template_v2.oid)
        self.assertEqual(str(cert_template_oid['templateMajorVersion'].native), template_v2.version.split('.')[0])
        self.assertEqual(str(cert_template_oid['templateMinorVersion'].native), template_v2.version.split('.')[1])


    def test_cms_util_with_san(self):
        subject_cn = "test.example.com"
        dns_names = ["test.example.com", "www.test.example.com", "api.test.example.com"]
        # 1) Build CRMF with SAN
        crmf_encoded = _build_crmf_with_san(subject_cn, dns_names)

        # 2) Build CMS
        ca_name = 'Authority'
        template_v1 = TemplateData('WebServer', 'temp_displ', '1', '1', '1.2.3')
        cms_b64 = create_cms(crmf_encoded, ca_name, template_v1)

        # 3) Parse CMS -> PKIData -> first TaggedRequest -> PKCS#10
        ci = cms.ContentInfo.load(base64.b64decode(cms_b64))
        pki_data = cmc.PKIData.load(ci['content']['encap_content_info']['content'].native)

        tagged_req = pki_data['reqSequence'][0]  # CMC TaggedRequest
        cert_request = tagged_req.chosen['certificationRequest']  # PKCS#10 object

        # Ensure we have an asn1crypto CSR object
        p10 = cert_request if isinstance(cert_request, csr.CertificationRequest) \
            else csr.CertificationRequest.load(cert_request.dump())

        # 4) Grab attributes (no .get() on asn1crypto sequences)
        cri = p10['certification_request_info']
        assert 'attributes' in cri, "CSR has no attributes"
        attrs = cri['attributes']

        # 5) Find pkcs#9 extensionRequest (1.2.840.113549.1.9.14)
        ext_req_attr = None
        for attr in attrs:
            if attr['type'].dotted == '1.2.840.113549.1.9.14':
                ext_req_attr = attr
                break
        assert ext_req_attr is not None, "extensionRequest attribute not found in CSR"

        # 6) Decode Extensions from the attribute value (object or raw bytes)
        exts_obj = ext_req_attr['values'][0]
        exts = x509.Extensions.load(exts_obj) if isinstance(exts_obj, (bytes, bytearray)) else exts_obj

        # 7) Locate SAN and verify DNS names
        san_ext = None
        for ext in exts:
            if ext['extn_id'].native == 'subject_alt_name':
                san_ext = ext
                break
        assert san_ext is not None, "SAN extension not found in extensionRequest"

        gns = san_ext['extn_value'].parsed  # GeneralNames
        got_dns = [gn.native for gn in gns if gn.name == 'dns_name']

        missing = set(dns_names) - set(got_dns)
        assert not missing, f"Missing SAN DNS entries: {missing}; got {got_dns}"
