# reactor_setup.py
import asyncio
from twisted.internet import asyncioreactor

asyncioreactor.install(asyncio.get_event_loop())
