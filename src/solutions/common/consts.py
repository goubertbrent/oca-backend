# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

OUR_CITY_APP_COLOUR = u'5BC4BF'

UNIT_PIECE = 1
UNIT_LITER = 2
UNIT_KG = 3
UNIT_GRAM = 4
UNIT_HOUR = 5
UNIT_MINUTE = 6
UNIT_DAY = 7
UNIT_PERSON = 8
UNIT_SESSION = 9
UNIT_PLATTER = 10
UNIT_WEEK = 11
UNIT_MONTH = 12
# values are the translation keys
UNITS = {
    UNIT_PIECE: 'piece',
    UNIT_LITER: 'liter',
    UNIT_KG: 'kilogram',
    UNIT_GRAM: 'gram',
    UNIT_HOUR: 'hour',
    UNIT_MINUTE: 'minute',
    UNIT_DAY: 'day',
    UNIT_WEEK: 'week',
    UNIT_MONTH: 'month',
    UNIT_PERSON: 'person',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

# values are translation keys except for the official symbols (liter, kg, gram, ..)
UNIT_SYMBOLS = {
    UNIT_PIECE: 'piece_short',
    UNIT_LITER: 'l',
    UNIT_KG: 'kg',
    UNIT_GRAM: 'g',
    UNIT_HOUR: 'h',
    UNIT_MINUTE: 'min',
    UNIT_DAY: 'day_short',
    UNIT_WEEK: 'week_short',
    UNIT_MONTH: 'month_short',
    UNIT_PERSON: 'person_short',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

ORDER_TYPE_SIMPLE = 1
ORDER_TYPE_ADVANCED = 2

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
SECONDS_IN_WEEK = 604800

CURRENCIES = ['EUR', 'USD', 'GBP', 'RON', 'TFT']
CURRENCY_NAMES = {
    'RON': u'Leu',
    'TFT': u'ThreeFold Token'
}


def get_currency_name(locale, currency_symbol):
    name = locale.currencies.get(currency_symbol)
    return name or CURRENCY_NAMES.get(currency_symbol, currency_symbol)


# Obtained by running openssl s_client -connect dev.payconiq.com:443 -showcerts | openssl x509 -text
PAYCONIQ_CERTIFICATES = {
    'https://api.payconiq.com': """-----BEGIN CERTIFICATE-----
MIIFbzCCBFegAwIBAgIQBB7tZDmIgq0Eu1Nfjl6lzTANBgkqhkiG9w0BAQsFADBw
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMS8wLQYDVQQDEyZEaWdpQ2VydCBTSEEyIEhpZ2ggQXNz
dXJhbmNlIFNlcnZlciBDQTAeFw0xNzAyMDcwMDAwMDBaFw0xOTA0MTcxMjAwMDBa
MHQxCzAJBgNVBAYTAk5MMRYwFAYDVQQIEw1Ob29yZC1Ib2xsYW5kMRIwEAYDVQQH
EwlBbXN0ZXJkYW0xHjAcBgNVBAoTFVBheWNvbmlxIEhvbGRpbmcgQi5WLjEZMBcG
A1UEAxMQYXBpLnBheWNvbmlxLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC
AQoCggEBAO3PgZenv41AU5/0LDTHg48r6yPImZd5KMTaIQsHtB5z/5dTYWLcwD7g
qD3dzS7e7bY4nCGhudZ94aGRazUjw2Q9TuShvcJW4eV+KaLVMhB3kR8pwnyYIDcq
yQtv++2UXAYWZZbIws0FEpNIgyHW1iEkKwL2Khy0xeApJPnNvQkWr2zeo1j0taLc
ZJAnSE68PoiIvjLK9wJFAtBAMcA607CwMqTd+b+ozsck38zuYfrqcqRlh/oAqid4
8Tq4D/dGu8pVFztgUypLaEv/Qvb/If+4coYK/W1VPsmLZm/cT/bO0QTs/LUGEthx
pKDNYSgg7llBGxHStwHSUAgQ80Rd8zkCAwEAAaOCAf8wggH7MB8GA1UdIwQYMBaA
FFFo/5CvAgd1PMzZZWRiohK4WXI7MB0GA1UdDgQWBBSV8XC1bkMVwnZeab3nQZdk
U1VmuTAxBgNVHREEKjAoghBhcGkucGF5Y29uaXEuY29tghR3d3cuYXBpLnBheWNv
bmlxLmNvbTAOBgNVHQ8BAf8EBAMCBaAwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsG
AQUFBwMCMHUGA1UdHwRuMGwwNKAyoDCGLmh0dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNv
bS9zaGEyLWhhLXNlcnZlci1nNS5jcmwwNKAyoDCGLmh0dHA6Ly9jcmw0LmRpZ2lj
ZXJ0LmNvbS9zaGEyLWhhLXNlcnZlci1nNS5jcmwwTAYDVR0gBEUwQzA3BglghkgB
hv1sAQEwKjAoBggrBgEFBQcCARYcaHR0cHM6Ly93d3cuZGlnaWNlcnQuY29tL0NQ
UzAIBgZngQwBAgIwgYMGCCsGAQUFBwEBBHcwdTAkBggrBgEFBQcwAYYYaHR0cDov
L29jc3AuZGlnaWNlcnQuY29tME0GCCsGAQUFBzAChkFodHRwOi8vY2FjZXJ0cy5k
aWdpY2VydC5jb20vRGlnaUNlcnRTSEEySGlnaEFzc3VyYW5jZVNlcnZlckNBLmNy
dDAMBgNVHRMBAf8EAjAAMA0GCSqGSIb3DQEBCwUAA4IBAQCw+DJTVTa9uYna8o2h
UmDpPW1DOxnk0TYfpklMuVAdFPZqFpdOmdr2aWPtkqbhVXmqCxok7PKuifvkdXpo
ZQD8vNLr5Lkz0X2UvA3nml754EXZinekhhMjSY41HvjZm93xLNiDLOx4zMuNUWvG
/pNBQIsFzVs4fBioUr1fp4HOrDyRj3gK6hPuVb69QKv4PgrszTxauAxdyHES+hiI
0hlE4GsaGW7uHzE4V49dHlK9vFGqS1vU29WEWb5ubAQsONMeZUUy4L8qCgICX1WO
2+Bs2k7TaPpNEey/4E1YiQFDIJfxgPe5d1hrH8UU2NZeNwNhRBCGYi8V/iQlTqbA
8buS
-----END CERTIFICATE-----""",
    'https://dev.payconiq.com': """-----BEGIN CERTIFICATE-----
MIIFVTCCBD2gAwIBAgIRALgxopAyxfuraSGpTuoWd4wwDQYJKoZIhvcNAQELBQAw
gZAxCzAJBgNVBAYTAkdCMRswGQYDVQQIExJHcmVhdGVyIE1hbmNoZXN0ZXIxEDAO
BgNVBAcTB1NhbGZvcmQxGjAYBgNVBAoTEUNPTU9ETyBDQSBMaW1pdGVkMTYwNAYD
VQQDEy1DT01PRE8gUlNBIERvbWFpbiBWYWxpZGF0aW9uIFNlY3VyZSBTZXJ2ZXIg
Q0EwHhcNMTgwMjE2MDAwMDAwWhcNMjEwMjE1MjM1OTU5WjBUMSEwHwYDVQQLExhE
b21haW4gQ29udHJvbCBWYWxpZGF0ZWQxFDASBgNVBAsTC1Bvc2l0aXZlU1NMMRkw
FwYDVQQDExBkZXYucGF5Y29uaXEuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEA0B04UziW/ZzDDw8Xf/4hQWPHaFPa52YF7h5NiDR8Tjee0KswY/Fo
+Vm35e3RR+Il8dPlDwlpJqqDbT6diUDgGUUO/Ou4XAhUTM0MLKv9p2g8DGq71/MV
Pe0xD80bPS/xi3mqwSTTIhvDt26mAOjGjSX838T9L4bmul5kS7KPUagoCnhV1kvX
QNcjAVFqchex08BCLCkJQxSYC6LLDDxrSWDp125lqZkN1GLRUJQu5NmAlvEC3i20
DXS1gMBZ6todc8SuzxuiIZVDFTsBjDheAyTErePwMicuF06VKir/AQ+XyCfa7Pxv
TgafPPhn40yR2UBL5tjZA0/ter1kpy/XTwIDAQABo4IB4zCCAd8wHwYDVR0jBBgw
FoAUkK9qOpRaC9iQ6hJWc99DtDoo2ucwHQYDVR0OBBYEFKLzbDvmzL7n5e1RPkU5
MK0RfEzeMA4GA1UdDwEB/wQEAwIFoDAMBgNVHRMBAf8EAjAAMB0GA1UdJQQWMBQG
CCsGAQUFBwMBBggrBgEFBQcDAjBPBgNVHSAESDBGMDoGCysGAQQBsjEBAgIHMCsw
KQYIKwYBBQUHAgEWHWh0dHBzOi8vc2VjdXJlLmNvbW9kby5jb20vQ1BTMAgGBmeB
DAECATBUBgNVHR8ETTBLMEmgR6BFhkNodHRwOi8vY3JsLmNvbW9kb2NhLmNvbS9D
T01PRE9SU0FEb21haW5WYWxpZGF0aW9uU2VjdXJlU2VydmVyQ0EuY3JsMIGFBggr
BgEFBQcBAQR5MHcwTwYIKwYBBQUHMAKGQ2h0dHA6Ly9jcnQuY29tb2RvY2EuY29t
L0NPTU9ET1JTQURvbWFpblZhbGlkYXRpb25TZWN1cmVTZXJ2ZXJDQS5jcnQwJAYI
KwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmNvbW9kb2NhLmNvbTAxBgNVHREEKjAoghBk
ZXYucGF5Y29uaXEuY29tghR3d3cuZGV2LnBheWNvbmlxLmNvbTANBgkqhkiG9w0B
AQsFAAOCAQEARAOcggCcdU35KTxh2jJbyUAMIlpDdP1UZlRS3QLTbAJUEEbEXdFt
mugc0rC/tstFxvjS4BLlYfjS5gXXPL1ql/PaQzslW7vlo/3J+75YWt67DTaWbh/+
IVa4VNjVS14r6xkUOajoM3H2RldjoSkKxUOQH+y9vK12vcl/vd2fzsQlfEEftm0E
aS5IUXknNRJM18YJelga0d283Ou3z7iri3XdaFx365CVC7ZYYD5IfIzgqHHLuqZQ
5uBvUb1pUFNzDQpkd9X0oB7gxIUPi2fx5D0KX3dwhoenf+17CPI5Ysapnv/r8FaW
4LWgEhIIbH8lI1QA+KiHWQeH+sIjMfJiuw==
-----END CERTIFICATE-----"""
}
