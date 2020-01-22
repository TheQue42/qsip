#import time

from qsip.ua import QSipUa


if __name__ == "__main__":
    method = "InVite"
    q = QSipUa()
    q.sendMessage(request_uri="sip:taisto@nisse.se", next_hop={"addr":"10.9.24.1", "port":5060},
                  msg_from={"uri": "kenneth@ip-s.se"},
                  msg_to={"uri": "taisto@ip-s.se"}, msg_body="hejsan")
    #q.testStuff()
    #m = [mm for mm in  if mm == method]
    print(method)
