# -*- coding: utf-8 -*-


from logic_pb2 import *
from server_pb2 import *


URI2CLASS = {
        1   :   FrontendPack,
}

CLASS2URI = {}
for uri, proto in URI2CLASS.items():
    CLASS2URI[proto] = uri

