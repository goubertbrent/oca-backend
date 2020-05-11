# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.6@@

import json

import mc_unittest
from rogerthat.bizz.payment.providers.threefold.api import _get_total_amount


class Test(mc_unittest.TestCase):

    def test_total_amount(self):
        transaction = json.loads(
            '{"hashtype":"transactionid","block":{"minerpayoutids":null,"transactions":null,"rawblock":{"parentid":"0000000000000000000000000000000000000000000000000000000000000000","timestamp":0,"pobsindexes":{"BlockHeight":0,"TransactionIndex":0,"OutputIndex":0},"minerpayouts":null,"transactions":null},"blockid":"0000000000000000000000000000000000000000000000000000000000000000","difficulty":"0","estimatedactivebs":"0","height":0,"maturitytimestamp":0,"target":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"totalcoins":"0","arbitrarydatatotalsize":0,"minerpayoutcount":0,"transactioncount":0,"coininputcount":0,"coinoutputcount":0,"blockstakeinputcount":0,"blockstakeoutputcount":0,"minerfeecount":0,"arbitrarydatacount":0},"blocks":null,"transaction":{"id":"bf30edbbf1042e12b11749ec9e40a15e31e785ec8ffb608f20fe5e944d14f4a0","height":108708,"parent":"6994bb8e340c65cd3bbb67d01e964f3b511f8afd639771294fefcb40b6df07fb","rawtransaction":{"version":0,"data":{"coininputs":[{"parentid":"0eb6c4cd7c787470e9bb892ec1dcb0f06d703cee28e77a3b1bfd0145272ca29c","unlocker":{"type":1,"condition":{"publickey":"ed25519:3127ae22f3d40743c48517b5321fa36f1452499e51e6319bbdee35b52439a6ee"},"fulfillment":{"signature":"1e7243644ba5a083bb941f66ef1f81645d42d333341e642d4dd0273e73790d41bb8db80566320d47d908a0db46681a76c7b5d256de56f619745515afabf6dd01"}}}],"coinoutputs":[{"value":"500000000","unlockhash":"0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb"},{"value":"68530000000","unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}],"minerfees":["100000000"]}},"coininputoutputs":[{"value":"69130000000","condition":{"type":1,"data":{"unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}},"unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}],"coinoutputids":["6f86e92fbc247d1340293928b290bf04a3bc9023218d4af106d81bf466ea2d2d","41cb058c3e8f5cf9abee42c40d31d6fe6319b91336adcfc41cc0ac6ed66c0b30"],"coinoutputunlockhashes":["0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb","01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"],"blockstakeinputoutputs":null,"blockstakeoutputids":null,"blockstakeunlockhashes":null},"transactions":null,"multisigaddresses":null,"unconfirmed":false}')
        service_address = u'0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb'
        total_amount = _get_total_amount(transaction, service_address)
        self.assertEqual(0.5 * pow(10, 9), total_amount)


    def test_total_amount2(self):
        transaction = json.loads(
            '{"hashtype":"transactionid","block":{"minerpayoutids":null,"transactions":null,"rawblock":{"parentid":"0000000000000000000000000000000000000000000000000000000000000000","timestamp":0,"pobsindexes":{"BlockHeight":0,"TransactionIndex":0,"OutputIndex":0},"minerpayouts":null,"transactions":null},"blockid":"0000000000000000000000000000000000000000000000000000000000000000","difficulty":"0","estimatedactivebs":"0","height":0,"maturitytimestamp":0,"target":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"totalcoins":"0","arbitrarydatatotalsize":0,"minerpayoutcount":0,"transactioncount":0,"coininputcount":0,"coinoutputcount":0,"blockstakeinputcount":0,"blockstakeoutputcount":0,"minerfeecount":0,"arbitrarydatacount":0},"blocks":null,"transaction":{"id":"a697be75f435e8a9fa2837dcf93b233ce6abd9ad71ffe13a857f313c3f290697","height":0,"parent":"0000000000000000000000000000000000000000000000000000000000000000","rawtransaction":{"version":0,"data":{"coininputs":[{"parentid":"41cb058c3e8f5cf9abee42c40d31d6fe6319b91336adcfc41cc0ac6ed66c0b30","unlocker":{"type":1,"condition":{"publickey":"ed25519:3127ae22f3d40743c48517b5321fa36f1452499e51e6319bbdee35b52439a6ee"},"fulfillment":{"signature":"3151dad4cc5df5167959a32f9fade7840ced8a1df73c3aa74b754f2b4b434e17fffdb057b239546556509cb8241f6a1155e218bfab700d38af26ad308e187c0f"}}}],"coinoutputs":[{"value":"500000000","unlockhash":"0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb"},{"value":"67930000000","unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}],"minerfees":["100000000"]}},"coininputoutputs":[{"value":"68530000000","condition":{"type":1,"data":{"unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}},"unlockhash":"01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"}],"coinoutputids":["a15e148cd10e4966a27800823150a18aae7d1818a4799608c3bc07ad41bf366f","390c06e44a2dd0eb7ce0ad5ef39c89de7d9ed409bc78f466407ce3566370f469"],"coinoutputunlockhashes":["0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb","01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99"],"blockstakeinputoutputs":null,"blockstakeoutputids":null,"blockstakeunlockhashes":null},"transactions":null,"multisigaddresses":null,"unconfirmed":true}')
        service_address = u'0198c17d14518655266986a55c6756dc3e79c0e7f49373f23ebaae7db9e67532ccea7043ebd9fb'
        total_amount = _get_total_amount(transaction, service_address)
        self.assertEqual(0.5 * pow(10, 9), total_amount)
