#!/usr/bin/env python3

__author__ = "Martin Landa"

from pywps.app.Service import Service

from processes.smoderp1d import Smoderp1d

processes = [
    Smoderp1d()
]

application = Service(
    processes,
    ['/opt/pywps/pywps.cfg']
)
