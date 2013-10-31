#-*- coding: utf-8 -*-
import SocketServer
import BaseHTTPServer


class ThreadingSimpleServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

