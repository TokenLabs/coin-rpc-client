# Copyright 2014, 2015 Token Labs LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from http.client import HTTPConnection
import json
import base64
import decimal

USER_AGENT = "CoinRpc"

class JSONRPCException(Exception):
    pass

class CoinRpc():

    def __init__(self, username, password, host, port, precision):

        self.host = host
        self.port = port
        self.next_id = 0
        self.precision = precision
        self.auth = "Basic " + base64.b64encode((username + ":" + password).encode()).decode()

    def call(self, *args):
       return self.batch([list(args)])[0]

    def batch(self, calls):

        batch_data = []
        for call in calls:
            m = call.pop(0)
            batch_data.append({
                "jsonrpc" : "2.0",
                "method"  : m,
                "params"  : call,
                "id"      : self.next_id
            })
            self.next_id += 1

        def encode_decimal(o):
            if isinstance(o, decimal.Decimal):
                return float(round(o, self.precision))
            raise TypeError(repr(o) + " is not JSON serializable")

        postdata = json.dumps(batch_data, default=encode_decimal)

        conn = HTTPConnection(self.host, self.port)

        try:

            conn.request("POST", "", postdata, {
                "Host" : self.host,
                "User-Agent" : USER_AGENT,
                "Authorization" : self.auth,
                "Content-Type" : "application/json"
            })

            response = conn.getresponse()

            if response is None:
                raise JSONRPCException({
                    'code': -342, 
                    'message': 'missing HTTP response from server'
                })

            if response.status is not 200:
                raise JSONRPCException({
                    'code': -344,
                    'message': str(response.status) + " " + response.reason
                })

            try:
                responses = json.loads(response.read().decode())
            except ValueError as e:
                raise JSONRPCException(str(e))

        finally:
            conn.close()

        results = []

        for response in responses:
            if response['error'] is not None:
                raise JSONRPCException(response['error'])
            elif 'result' not in response:
                raise JSONRPCException({
                    'code': -343, 
                    'message': 'missing JSON-RPC result'
                })
            else:
                results.append(response['result'])

        return results

