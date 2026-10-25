#!/usr/bin/env python3

__author__ = "Martin Landa"

from pywps.app.Service import Service

from processes.profile1d import Profile1d
from processes.smoderp2d import Smoderp2d

processes = [
    Profile1d(),
    Smoderp2d()
]

application = Service(
    processes,
    ['/opt/pywps/pywps.cfg']
)
