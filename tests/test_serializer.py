# VMware vSphere Python SDK
# Copyright (c) 2008-2014 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import tests
import vcr


from pyVmomi import SoapStubAdapter
from pyVmomi import vim
from pyVmomi.VmomiSupport import GetRequestContext


class SerializerTests(tests.VCRTestBase):

    def _base_serialize_test(self, soap_creator, request_matcher):
        my_vcr = vcr.VCR()
        my_vcr.register_matcher('request_matcher', request_matcher)

        with my_vcr.use_cassette(
                'test_simple_request_serializer.yaml',
                cassette_library_dir=tests.fixtures_path,
                record_mode='none',
                match_on=['request_matcher']) as cass:
            stub = soap_creator()
            si = vim.ServiceInstance("ServiceInstance", stub)
            content = si.RetrieveContent()
            self.assertTrue(content is not None)
            self.assertTrue(
                '<_this type="ServiceInstance">ServiceInstance</_this>'
                in cass.requests[0].body)

    def _body_request_matcher(self, r1, r2):
        soap_msg = ('<soapenv:Body>'
                    '<RetrieveServiceContent xmlns="urn:vim25">'
                    '<_this type="ServiceInstance">'
                    'ServiceInstance'
                    '</_this>'
                    '</RetrieveServiceContent>'
                    '</soapenv:Body>')
        if soap_msg in r1.body:
            return True
        raise SystemError('serialization error occurred')

    def _request_context_request_matcher(self, r1, r2):
        request_context = ('<soapenv:Header><vcSessionCookie>123456789</vcSessionCookie></soapenv:Header>')
        if request_context in r1.body:
            return True
        raise SystemError('serialization error occurred')

    def test_simple_request_serializer(self):
        def soap_creator():
            return SoapStubAdapter('vcsa', 443)
        self._base_serialize_test(soap_creator, self._body_request_matcher)

    def test_request_context_serializer_instance(self):
        def request_matcher(r1, r2):
            return self._request_context_request_matcher(r1, r2) and self._body_request_matcher(r1, r2)
        def soap_creator():
            return SoapStubAdapter('vcsa', 443, requestContext={'vcSessionCookie': '123456789'})
        self._base_serialize_test(soap_creator, request_matcher)

    def test_request_context_serializer_global(self):
        def request_matcher(r1, r2):
            return self._request_context_request_matcher(r1, r2) and self._body_request_matcher(r1, r2)
        def soap_creator():
            return SoapStubAdapter('vcsa', 443)
        GetRequestContext()['vcSessionCookie'] = '123456789'
        try:
            self._base_serialize_test(soap_creator, request_matcher)
        finally:
            GetRequestContext().pop("vcSessionCookie")
