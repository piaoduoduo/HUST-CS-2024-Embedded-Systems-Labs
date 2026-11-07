"""Temporary pairing agent restricted to the user's identified lab phone.
BlueZ API: https://bluez.readthedocs.io/en/latest/agent-api/
"""
import dbus,dbus.service,dbus.mainloop.glib,signal
from gi.repository import GLib
PHONE='/org/bluez/hci0/dev_00_11_22_33_44_55'
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus=dbus.SystemBus();loop=GLib.MainLoop()
class Rejected(dbus.DBusException):_dbus_error_name='org.bluez.Error.Rejected'
def check(device):
    if str(device)!=PHONE:raise Rejected('Only the authorized lab phone is accepted')
class Agent(dbus.service.Object):
    @dbus.service.method('org.bluez.Agent1',in_signature='',out_signature='')
    def Release(self):loop.quit()
    @dbus.service.method('org.bluez.Agent1',in_signature='o',out_signature='')
    def RequestAuthorization(self,device):check(device);print('Authorized pairing',device,flush=True)
    @dbus.service.method('org.bluez.Agent1',in_signature='ou',out_signature='')
    def RequestConfirmation(self,device,passkey):check(device);print('Authorized phone confirmation',str(passkey).zfill(6),flush=True)
    @dbus.service.method('org.bluez.Agent1',in_signature='os',out_signature='')
    def AuthorizeService(self,device,uuid):
        check(device)
        if str(uuid).lower()!='00001101-0000-1000-8000-00805f9b34fb':raise Rejected('SPP only')
        print('Authorized SPP',device,flush=True)
    @dbus.service.method('org.bluez.Agent1',in_signature='',out_signature='')
    def Cancel(self):print('Pairing request canceled',flush=True)
agent=Agent(bus,'/lab5/phone_agent')
manager=dbus.Interface(bus.get_object('org.bluez','/org/bluez'),'org.bluez.AgentManager1')
adapter=dbus.Interface(bus.get_object('org.bluez','/org/bluez/hci0'),'org.freedesktop.DBus.Properties')
manager.RegisterAgent('/lab5/phone_agent','NoInputNoOutput')
manager.RequestDefaultAgent('/lab5/phone_agent')
adapter.Set('org.bluez.Adapter1','Pairable',dbus.Boolean(True))
adapter.Set('org.bluez.Adapter1','DiscoverableTimeout',dbus.UInt32(600))
adapter.Set('org.bluez.Adapter1','Discoverable',dbus.Boolean(True))
signal.signal(signal.SIGTERM,lambda *_:loop.quit())
GLib.timeout_add_seconds(600,lambda:loop.quit())
print('READY: authorized phone only; expires in 10 minutes',flush=True)
try:loop.run()
finally:
    adapter.Set('org.bluez.Adapter1','Discoverable',dbus.Boolean(False))
    adapter.Set('org.bluez.Adapter1','Pairable',dbus.Boolean(False))
    manager.UnregisterAgent('/lab5/phone_agent')
