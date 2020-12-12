#!/usr/bin/env python3

__author__ = "Martin Landa"

from pywps.app.Service import Service

from processes.smoderp1d import Smoderp1d
from processes.smoderp2d import Smoderp2d

processes = [
    Smoderp1d(),
    Smoderp2d()
]

application = Service(
    processes,
    ['/opt/pywps/pywps.cfg']
)
