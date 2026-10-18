from django.test import SimpleTestCase


class WinrmTransportConfigurationCallbackTests(SimpleTestCase):

    def test_credssp_returns_empty_attribute_list(self):
        response = self.client.get("/v1/callbacks/authority/winrmConfig/PyADCS-WinRM/credssp")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_unknown_transport_returns_400(self):
        response = self.client.get("/v1/callbacks/authority/winrmConfig/PyADCS-WinRM/ntlm")

        self.assertEqual(response.status_code, 400)

    def test_unknown_kind_returns_400(self):
        response = self.client.get("/v1/callbacks/authority/winrmConfig/Other/credssp")

        self.assertEqual(response.status_code, 400)
