import winrm
from django.test import TestCase

from PyADCSConnector.utils.dump_parser import DumpParser


class DumpParserTest(TestCase):
    def test_parse_certificates(self):
        data = """

RequestID                  : 710
Request.StatusCode         : 0
Request.DispositionMessage : Issued
Request.RequesterName      : EXAMPLE\\test.user
Request.SubmittedWhen      : 7/7/2023 9:35:52 AM
Request.CommonName         :
CertificateTemplate        : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.2517003.8444064
RawCertificate             : MIIC7jCCAdagAwIBAgIUAsZlsQB5UD4DCM8nOeSFarWweicwDQYJKoZIhvcNAQEL
                             BQAwMTEYMBYGA1UECgwPRXhhbXBsZSBDb21wYW55MRUwEwYDVQQDDAx1c2VyLmV4
                             YW1wbGUwHhcNMjQwMTAxMDAwMDAwWhcNMjYwMTAxMDAwMDAwWjAxMRgwFgYDVQQK
                             DA9FeGFtcGxlIENvbXBhbnkxFTATBgNVBAMMDHVzZXIuZXhhbXBsZTCCASIwDQYJ
                             KoZIhvcNAQEBBQADggEPADCCAQoCggEBAJEwmwo0lrhrJAl+rtE2lajCu/XZPzqQ
                             jxT0d/CzKzWads49ItbqQuU5ab070knMPqVgKz7rW5qlIfYW5xFUNmiaWXJMk3hA
                             hMbuZd5jIFd3uuKe/Nil49tj9Bv3polSDetygfa4yuBlPTl2LFl8R4s85gXL6Qku
                             pptXK1L1bWU7p+Rss0yJxrVKJibyW3wtTnet5acO8hHULXGRvxsZ2s9jgd4n05dB
                             Rwb7i5K+TAPasxXuE2FFtGOAME422kwH58bf9fBYh6x9eku8xnWto9YbM/MTctTy
                             ssf4FE6BYvfID8PftuN5JHlrxGv778/8852OX1x7NkEEhhVrIGoUlD0CAwEAATAN
                             BgkqhkiG9w0BAQsFAAOCAQEAYBcvytk888ALyTRkQdY71ldwzmRcjmxeJcqgUlrK
                             jvgia4IzFg+CP1iyMlsv3h1bbjoM4I0+4VCE6FTVwDij5N0yaMqa1j83FbcYmuTY
                             PtPS9NmUS7C40n3+GoA/TenhiHAqTYT+JR/+DYo1tWz14wHGSfzTpES7A48WRN8S
                             ayh8J7iokwYGATtu/nl9V8t1uOezEt/JaorvPLFZr53BX+lRTwPRML/a17c4TJYn
                             4CoCAk+V+9stXtnfcUT2CTZr0Vu5oNIOgav8n0ccaEI3Yzy5+ps6xR37J4JvOFXP
                             /ywT1580mDN7oK8xhu5khDOseGoDSar+NCtu74HhSQW/5g==
CertificateTemplateOid     : Certificate authentication external client
                             (1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.2517003.8444064)
RowId                      : 710
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 710], [Request.StatusCode, 0], [Request.DispositionMessage, Issued],
                             [Request.RequesterName, EXAMPLE\\test.user]...}

RequestID                  : 716
Request.StatusCode         : 0
Request.DispositionMessage : Issued
Request.RequesterName      : EXAMPLE\\test.user
Request.SubmittedWhen      : 8/18/2023 9:56:15 AM
Request.CommonName         : Example User
CertificateTemplate        : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.2517003.8444064
RawCertificate             : MIIC7jCCAdagAwIBAgIUcHjP1DpGLXAyoKdFZ/COJC8FEgEwDQYJKoZIhvcNAQEL
                             BQAwMTEYMBYGA1UECgwPRXhhbXBsZSBDb21wYW55MRUwEwYDVQQDDAxFeGFtcGxl
                             IFVzZXIwHhcNMjQwMTAxMDAwMDAwWhcNMjYwMTAxMDAwMDAwWjAxMRgwFgYDVQQK
                             DA9FeGFtcGxlIENvbXBhbnkxFTATBgNVBAMMDEV4YW1wbGUgVXNlcjCCASIwDQYJ
                             KoZIhvcNAQEBBQADggEPADCCAQoCggEBAPDcbhf7fvOACrqZdaBb4CrX/NGKESjE
                             akVB+VBwNp/G/TNIoV9/dQJCcB0gSIkbb6l9dF6QKCBBdedwLUyX3zRdCaaorfTV
                             Mj1xGqQC55mBoej/pq0DT6XFoB7xkmWpHgVHXmvVkIrM2QsCH3Cw9vSvP2oADZ4Y
                             Tr9VHGfMLcQtUmPKXIZz5CW5ZbyywgV/3Hs8zoIXjo8UD5LYEiQqjtOrN2o08cTP
                             W9EmEJ4dAAECui+E7NyFre7hT3rVcLnz9bV48CVEKgCIm/VdlMACwlC7MbEzRcZF
                             rO9YwV4d4KYJjf8JsTCwWfdySyDc4WJSbQ4UJqsCvNI7FQRjAHgDNbcCAwEAATAN
                             BgkqhkiG9w0BAQsFAAOCAQEAbWbBA38ln2sMIrVNzYa5Xg1Br8Brut8RM/vN388s
                             SUnTWljy44vJx94hn40FbghTEwCqF3+LZ07CAnMfIB0Si9f0Ch0fy7+83+2H/HSB
                             /9wZyzRy1FOJvL7z2lSkZ6j4Ae1puJwCaPbEjb34hdYZ0zGc9x+8FI2RTQeZfdr2
                             fuDVfZ8IMcq5Cmln47D+g5RH6F1/LpP/as4weZJ1vkXvyfJclt8umu4sI2YWkIGH
                             5QbTAcVQfwntKh2nvfRSMkQZLmnO1PlSiXLkc58GJroQGEHcKlBcpxfkqlbRBUeH
                             x7IABqao3x1JvS3kMcfD2qCA2lRvzSmD6NIkA2O5wVbL3g==
CertificateTemplateOid     : Certificate authentication external client
                             (1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.2517003.8444064)
RowId                      : 716
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 716], [Request.StatusCode, 0], [Request.DispositionMessage, Issued],
                             [Request.RequesterName, EXAMPLE\\test.user]...}

RequestID                  : 787
Request.StatusCode         : 0
Request.DispositionMessage : Issued
Request.RequesterName      : EXAMPLE\\HOST01$
Request.SubmittedWhen      : 12/28/2023 12:26:31 PM
Request.CommonName         : host.example.com
CertificateTemplate        : WebServer
RawCertificate             : MIIC9jCCAd6gAwIBAgIUVjYeYnJoiwqJAmpkyxXw0vae4dYwDQYJKoZIhvcNAQEL
                             BQAwNTEYMBYGA1UECgwPRXhhbXBsZSBDb21wYW55MRkwFwYDVQQDDBBob3N0LmV4
                             YW1wbGUuY29tMB4XDTI0MDEwMTAwMDAwMFoXDTI2MDEwMTAwMDAwMFowNTEYMBYG
                             A1UECgwPRXhhbXBsZSBDb21wYW55MRkwFwYDVQQDDBBob3N0LmV4YW1wbGUuY29t
                             MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwXZ2gasHi+0EurzrVpOc
                             tZ83grXDuw81fPEAOybEZhQNY8JDAjL9KtJUz7biANnoOobW4QFGz1t9BAL3Lt3e
                             YIUnHLIVXKxfvS9knYVfisN4UN7EEmzpzbH0wlBj2FuQIFInHNdtr8JzxXSX0g9o
                             ce+3Qv5AB1grLdY7HF3a89xj+rCP5WXHMkOYUpXziGzXM05wHqpRvOC2riebmXs3
                             lqd8OcALifi2s4J8Pi84pEo3QWM0w+SLBpD2BeG2yuyY9norxg+fJEIJODtwioV0
                             DsaYmDXC0m/VHTBi4F6xWEnzGnd0A7XKsNzRt5+f69fa87/tspFk+07r8dtOzQo9
                             ZwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQCrdynwHvazxNnyFWER/P8lFcgIcpTc
                             7+c9jmrY1FPOT8SmRdcShVN6d1TL5K3RXEDs0Q1Ouc1epP9Uc87gqHWCtwAQzdCJ
                             P4qTuK0ZUl2PWfQEAUQCEQhx2+jcsZWkPdPo8rTBoNoHiJE6F8UOvVWDE96Bm3e7
                             56jwwN1MuFTbRuBJ7odhjhqiv2jIy1U8iVnBgfHATjTbGSR1MLNr1/cxSqi7JnXH
                             yb/ON0AdoI3gLr6XcXMovw8js90goeZA4NhxKrlyzzRWoEMD0l8UvRkqOkyzDMEc
                             H0zl9iGHt72MR3adUuSpQYxLaoR5q2TbHA1EZX/OYnWn9MYnPeL/EEC+
CertificateTemplateOid     : WebServer
RowId                      : 787
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 787], [Request.StatusCode, 0], [Request.DispositionMessage, Issued], 
                             [Request.RequesterName, EXAMPLE\\HOST01$]...}
RequestID                  : 788
Request.StatusCode         : 0
Request.DispositionMessage : Revoked by EXAMPLE\\test.user
Request.RequesterName      : EXAMPLE\\test.user
Request.SubmittedWhen      : 12/30/2023 2:17:34 PM
Request.CommonName         : signserver-ra-01
CertificateTemplate        : WebServer
RawCertificate             : MIIC9jCCAd6gAwIBAgIUDln83rjRZIv/HUBxseHRwJhT2XcwDQYJKoZIhvcNAQEL
                             BQAwNTEYMBYGA1UECgwPRXhhbXBsZSBDb21wYW55MRkwFwYDVQQDDBBzaWduc2Vy
                             dmVyLXJhLTAxMB4XDTI0MDEwMTAwMDAwMFoXDTI2MDEwMTAwMDAwMFowNTEYMBYG
                             A1UECgwPRXhhbXBsZSBDb21wYW55MRkwFwYDVQQDDBBzaWduc2VydmVyLXJhLTAx
                             MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqETs9Zu9R9Byu6OukWQn
                             liVPavpBj8sCJsBtgJFf1FJFqIgESPapZ0UKmPoYVL5UjQSMfxvLDPoo+BIecRAQ
                             5dXT1YTbuMedgqIvFTD31Cb/tEEGzjvHb/XzoyyRwBMmMNwuXxpLxdH8fg1rlsKq
                             rNOWaMlvRM2je6IF7z0U7mQlQtDJtmCW57LjiDW2/ZkifNTJ5XqRM3wN/BOhmtcV
                             ZnuVDi92OzhZ7+e8MGHTsGQnBaPQBMkriNTR3p4JGPDgtu8vRPmi4h3Gh/PiSnD9
                             oi3lZUvCZFemDcdV1MzY3D4JaPtBrDGO7OqPnaNOj8Y3TqGJsRNhB4COw5WKOIzV
                             KwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQBNJmlRvGKT43ZcCiNsEHYMKbTSnJ+w
                             HRJ8gdCcFGcNJbqN22ujGIYrDfxkvonaAjxURSe4Y3gP4CEapsyhoPwZlsgv6n2i
                             7bITBOoQHOsp3o6LTPowRYlnmpxaRaFk/1gcT0xhf4tK4bJuICM+Vs8pB/rmiQ8r
                             N3hY/8ZXLrCtoFKrzD4CXr3fr/OsYAZkTBlMvB3hTii5qZtLSXsJXdYsAZrYoYtM
                             /ZL04BxgmHU/PFdlG9JKM5vIEu9Ujl3uSMNdEpSE44/TC45E3gXVq60FCEBmdEGx
                             qGG02GZpsDLXt4suwZWMynTdeWfKWAlGsheuK/PYmDk+XkYGAaky506O
CertificateTemplateOid     : WebServer
RowId                      : 788
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 788], [Request.StatusCode, 0], [Request.DispositionMessage, Revoked by 
                             EXAMPLE\\test.user], [Request.RequesterName, EXAMPLE\\test.user]...}
RequestID                  : 789
Request.StatusCode         : 0
Request.DispositionMessage : Issued
Request.RequesterName      : EXAMPLE\\test.user
Request.SubmittedWhen      : 12/31/2023 9:33:55 AM
Request.CommonName         : testpy
CertificateTemplate        : WebServer
RawCertificate             : MIIC4jCCAcqgAwIBAgIUZVqjqD3WACkgkQp3smyX+tNPYRcwDQYJKoZIhvcNAQEL
                             BQAwKzEYMBYGA1UECgwPRXhhbXBsZSBDb21wYW55MQ8wDQYDVQQDDAZ0ZXN0cHkw
                             HhcNMjQwMTAxMDAwMDAwWhcNMjYwMTAxMDAwMDAwWjArMRgwFgYDVQQKDA9FeGFt
                             cGxlIENvbXBhbnkxDzANBgNVBAMMBnRlc3RweTCCASIwDQYJKoZIhvcNAQEBBQAD
                             ggEPADCCAQoCggEBAJ7j0ciHsXQIUZr4lyO+dV64680pcZbcee3c+qk6XAItiY1y
                             sy++CipydY9JNd5inxineLuXxjSnRiZAJ8z6wGrZxqJi1iPRfzmNNnOUL6KwZcmP
                             q3KM1oDPSUhio2PCIWAJF7or5zTq7iLLDpzrRPwhB2/5oZ4nCR39MXiJBd8zOFTa
                             un1UmMr9BpvkOqEPo0BkJf6q9KJPYh+W2Pi2+qtVG4PigBJox3jJBOrCtIQcaGdk
                             g12o0TctgrnOOFg6KoerVi/Qaq+pscfJ68SLK5O1AQrYyQvMgfW4z88ypfTRkOPU
                             XuhrwZ9GmEFyeRC0Xo5LAkukTKrwmGbgM5+oRuECAwEAATANBgkqhkiG9w0BAQsF
                             AAOCAQEARezs+rwJtutxCfnrgimg2uGgRMM+VhnTYWJ+psN718+Yuh54CmRzSxkH
                             FWs5RoswTJRIIHj85QnWs+IlM8LswFP/sOWSbYyjKuZZWcHoD50B9WhTL3Ea6VQ/
                             Y4/DCgiEqQ8t0uiRB2Rur/AxFlXzf13nsoVo7jcBYDS5H0UbnAxnjTf9VBIVnOa2
                             qLlyr0rpNyao1k2Z+J+V8Lb8sDyL7e3fw8ZahX7YaF/e0w5lsQoV4oMpgpdYARaU
                             hFZIiqSx2bwI6i7t6LuycxhlgH5zN23Z3rH+n7a57PqQkcAJ5o0v0kebIwz4bJiJ
                             Nri+SQAeD45ObFYKgD0s9Z07ofABGQ==
CertificateTemplateOid     : WebServer
RowId                      : 789
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 789], [Request.StatusCode, 0], [Request.DispositionMessage, Issued], 
                             [Request.RequesterName, EXAMPLE\\test.user]...}

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_certificates(result)
        self.assertEqual(len(templates), 5)
        self.assertEqual(templates[2].template, "WebServer")

    def test_parse_template(self):
        data = """
        
Name          : TestofEnrollmentAgent
DisplayName   : Test of Enrollment Agent
SchemaVersion : 4
Version       : 100.3
OID           : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.8007785.10868302

Name          : User
DisplayName   : User
SchemaVersion : 1
Version       : 3.1
OID           : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.1.1

Name          : UserSignature
DisplayName   : User Signature Only
SchemaVersion : 1
Version       : 4.1
OID           : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.1.2

Name          : WebServer
DisplayName   : Web Server
SchemaVersion : 1
Version       : 4.1
OID           : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.1.16

Name          : Workstation
DisplayName   : Workstation Authentication
SchemaVersion : 2
Version       : 101.0
OID           : 1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.1.30

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_template_data(result)
        self.assertEqual(len(templates), 5)
        self.assertEqual(templates[0].name, "TestofEnrollmentAgent")
        self.assertEqual(templates[1].display_name, "User")
        self.assertEqual(templates[2].schema_version, "1")
        self.assertEqual(templates[3].version, "4.1")
        self.assertEqual(templates[4].oid, "1.3.6.1.4.1.311.21.8.16335329.656368.4341948.8708353.10624234.204.1.30")

    def test_parse_identified_certificates(self):
        data = """

RequestID                  : 810
Request.StatusCode         : 0
Request.DispositionMessage : Issued
Request.RequesterName      : EXAMPLE\\test.user
Request.SubmittedWhen      : 1/8/2024 4:56:32 PM
Request.CommonName         : signserver-ra-01
CertificateTemplate        : WebServer
SerialNumber               : 180000032a9a1aac7197589cef00000000032a
CertificateTemplateOid     : WebServer
RowId                      : 810
ConfigString               : ca.example.local\\Example Sub CA
Table                      : Request
Properties                 : {[RequestID, 810], [Request.StatusCode, 0], [Request.DispositionMessage, Issued], 
                             [Request.RequesterName, EXAMPLE\\test.user]...}

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_identified_certificates(result)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].certificate_template, "WebServer")
        self.assertEqual(templates[0].serial_number, "180000032a9a1aac7197589cef00000000032a")
        self.assertEqual(templates[0].config_string, "ca.example.local\\Example Sub CA")

    def test_parse_authority_data(self):
        data = """

Name                 : Example Sub CA
DisplayName          : Example Sub CA
ComputerName         : ca.example.local
ConfigString         : ca.example.local\\Example Sub CA
DistinguishedName    : CN=Example Sub CA,CN=Enrollment Services,CN=Public Key
                       Services,CN=Services,CN=Configuration,DC=example,DC=local
Type                 : Enterprise Subordinate CA
IsEnterprise         : True
IsRoot               : False
OperatingSystem      : Microsoft Windows Server 2016 Datacenter
IsAccessible         : True
RegistryOnline       : True
ServiceStatus        : Running
SetupStatus          : ServerInstall, ClientInstall, SecurityUpgraded, ServerIsUptoDate
Certificate          : [Subject]
                         O=Example Company, CN=Example Sub CA

                       [Issuer]
                         O=Example Company, CN=Example Root CA

                       [Serial Number]
                         656879DC6DFCC35C431488317DDB331F486A3847

                       [Not Before]
                         10/13/2019 8:33:12 AM

                       [Not After]
                         10/9/2034 8:33:12 AM

                       [Thumbprint]
                         66829B517CB2169DCB015988DA72DE6B7A7D75DA

BaseCRL              :
DeltaCRL             :
EnrollmentServiceURI :
EnrollmentEndpoints  : {https://ca.example.local/Example%20Sub%20CA_CES_Kerberos/service.svc/CES}

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_authority_data(result)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "Example Sub CA")
        self.assertEqual(templates[0].display_name, "Example Sub CA")
        self.assertEqual(templates[0].computer_name, "ca.example.local")
        self.assertEqual(templates[0].config_string, "ca.example.local\\Example Sub CA")
        self.assertEqual(templates[0].ca_type, "Enterprise Subordinate CA")
        self.assertEqual(templates[0].is_enterprise, True)
        self.assertEqual(templates[0].is_root, False)
        self.assertEqual(templates[0].is_accessible, True)
        self.assertEqual(templates[0].service_status, "Running")

    def test_parse_authority_data_2(self):
        data = """

Name                : TEST CA 02 Class B
DisplayName         : TEST CA 02 Class B
ComputerName        : ca.pki.local
ConfigString        : ca.pki.local\\TEST CA 02 Class B
DistinguishedName   : CN=TEST CA 02 Class B,CN=Enrollment Services,CN=Public Key Services,CN=Ser
                      vices,CN=Configuration,DC=pki,DC=local
Type                : Enterprise Subordinate CA
IsEnterprise        : True
IsRoot              : False
OperatingSystem     : Microsoft Windows Server 2019 Standard
IsAccessible        : True
RegistryOnline      : True
ServiceStatus       : Running
SetupStatus         : ServerInstall, SecurityUpgraded, ServerIsUptoDate
Certificate         : [Subject]
                        CN=TEST 02 Class B, OU=IT
                      
                      [Issuer]
                        CN=TEST Root CA, OU=IT
                      
                      [Serial Number]
                        5600000002B50D8D92CDA3907F000000000002
                      
                      [Not Before]
                        3. 10. 2023 11:59:59
                      
                      [Not After]
                        3. 10. 2029 12:09:59
                      
                      [Thumbprint]
                        04EE41322E5F2F3187AF13C40CA95B40BBA082FB
                      
EnrollmentEndpoints : {}

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_authority_data(result)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "TEST CA 02 Class B")
        self.assertEqual(templates[0].display_name, "TEST CA 02 Class B")
        self.assertEqual(templates[0].computer_name, "ca.pki.local")
        self.assertEqual(templates[0].config_string, "ca.pki.local\\TEST CA 02 Class B")
        self.assertEqual(templates[0].ca_type, "Enterprise Subordinate CA")
        self.assertEqual(templates[0].is_enterprise, True)
        self.assertEqual(templates[0].is_root, False)
        self.assertEqual(templates[0].is_accessible, True)
        self.assertEqual(templates[0].service_status, "Running")

    def test_parse_authority_data_3(self):
        data = """

Name          : EXAMPLE-LAB-CA1
DisplayName   : EXAMPLE-LAB-CA1
ComputerName  : labca1.example.local
ConfigString  : labca1.example.local\\EXAMPLE-LAB-CA1
Type          :
IsEnterprise  : False
IsRoot        : False
IsAccessible  : False
ServiceStatus :

        """
        protocol_output = bytes(data, 'utf-8'), bytes(data, 'utf-8'), 0
        result = winrm.Response(protocol_output)
        templates = DumpParser.parse_authority_data(result)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "EXAMPLE-LAB-CA1")
        self.assertEqual(templates[0].display_name, "EXAMPLE-LAB-CA1")
        self.assertEqual(templates[0].computer_name, "labca1.example.local")
        self.assertEqual(templates[0].config_string, "labca1.example.local\\EXAMPLE-LAB-CA1")
        self.assertEqual(templates[0].ca_type, "")
        self.assertEqual(templates[0].is_enterprise, False)
        self.assertEqual(templates[0].is_root, False)
        self.assertEqual(templates[0].is_accessible, False)
        self.assertEqual(templates[0].service_status, "")
