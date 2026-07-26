"""
URL configuration for pyadcs_connector project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from PyADCSConnector.views import info, health, attributes, authority_instance, callbacks, discovery_history, \
    certificate_management

urlpatterns = [
    path("v1", info.get_endpoints),
    path("v1/health", health.get_health),

    # Attributes interfaces
    path("v1/authorityProvider/<str:kind>/attributes",
         attributes.get_authority_attributes),
    path("v1/authorityProvider/<str:kind>/attributes/validate",
         attributes.validate_authority_attributes),

    # Authority management interfaces
    path("v1/authorityProvider/authorities",
         authority_instance.authority_operations),
    path("v1/authorityProvider/authorities/<str:uuid>",
         authority_instance.authority_instance_operations),
    path("v1/authorityProvider/authorities/<str:uuid>/raProfile/attributes",
         attributes.get_raprofile_attributes),
    path("v1/authorityProvider/authorities/<str:uuid>/raProfile/attributes/validate",
         attributes.validate_raprofile_attributes),

    # Certificate management interfaces
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/issue/attributes",
         attributes.get_issue_attributes),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/issue/attributes/validate",
         attributes.validate_issue_attributes),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/revoke/attributes",
         attributes.get_revoke_attributes),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/revoke/attributes/validate",
         attributes.validate_revoke_attributes),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/issue",
         certificate_management.issue_certificate),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/renew",
         certificate_management.renew_certificate),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/revoke",
         certificate_management.revoke_certificate),
    path("v2/authorityProvider/authorities/<str:uuid>/certificates/identify",
         certificate_management.identify_certificate),

    # Discovery interfaces
    path("v1/discoveryProvider/<str:kind>/attributes", attributes.get_discovery_attributes),
    path("v1/discoveryProvider/<str:kind>/attributes/validate", attributes.validate_discovery_attributes),
    path("v1/discoveryProvider/discover", discovery_history.start_discovery),
    path("v1/discoveryProvider/discover/<str:uuid>", discovery_history.discovery_operations),

    # Authority Callbacks
    path("v1/callbacks/authority/winrmConfig/<str:kind>/<str:winrm_transport>",
         callbacks.get_winrm_transport_configuration),
    # Discovery Callbacks
    path("v1/callbacks/discovery/listCertificateAuthority/<str:authority_instance_uuid>", callbacks.get_ca_names),
    path("v1/callbacks/discovery/listTemplate/<str:authority_instance_uuid>", callbacks.get_template_names),
    path("v1/callbacks/discovery/caSelect/<str:ca_select_method>/<str:authority_instance_uuid>",
         callbacks.get_discovery_ca_select_configuration),
    # RA Profile Callbacks
    path("v1/callbacks/raProfile/caSelect/<str:ca_select_method>/<str:authority_instance_uuid>",
         callbacks.get_raprofile_ca_select_configuration),
]
