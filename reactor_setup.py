# reactor_setup.py
import asyncio
from twisted.internet import asyncioreactor

asyncioreactor.install()
