# Boom EQ Client

This is a client library for the [Boom equalizer for Mac](
http://www.globaldelight.com/boom/index.php).

I like to programmatically control the EQ preset and set it depending on which
output I'm connected to  (e.g. different preset for headphones, bluetooth
speaker, etc.) I reverse engineered the communication from inspecting the
packets between the Boom Remote iOS app and the Boom service running on my
Mac.

## Usage
Boom Remote must be enabled on the Boom server:

<img src="https://user-images.githubusercontent.com/1694586/30945468-880e6c26-a3cc-11e7-827c-74a8a2a40598.png" width="200">


No arguments means connect to first available Boom server (Allow/Disallow
prompt appears on Mac, and little green light on Boom tray icon appears):
```python
In [1]: from boom_client import Boom

In [2]: client = Boom()
2017-09-27 19:26:29,872 INFO Found 1.6.1-sup-rmbp13._boom2._tcp.local. service: ServiceInfo(type='_boom2._tcp.local.', name='1.6.1-sup-rmbp13._boom2._tcp.local.', address='192.168.1.163', port=56962, weight=0, priority=0, server='rmbp13.local.', properties={})
2017-09-27 19:26:29,873 INFO Using first boom host found: ServiceInfo(type='_boom2._tcp.local.', name='1.6.1-sup-rmbp13._boom2._tcp.local.', address='192.168.1.163', port=56962, weight=0, priority=0, server='rmbp13.local.', properties={})
2017-09-27 19:26:29,874 INFO Login result: Accepted
```

You can also use any of the attributes for the service to specify which server (if you have more than one):
```python
In [3]: client = Boom(server='rmbp13.local.')
2017-09-27 21:43:26,022 INFO Found 1.6.1-sup-rmbp13._boom2._tcp.local. service: ServiceInfo(type='_boom2._tcp.local.', name='1.6.1-sup-rmbp13._boom2._tcp.local.', address='192.168.1.163', port=58990, weight=0, priority=0, server='rmbp13.local.', properties={})
2017-09-27 21:43:26,035 INFO Using first boom host found: ServiceInfo(type='_boom2._tcp.local.', name='1.6.1-sup-rmbp13._boom2._tcp.local.', address='192.168.1.163', port=58990, weight=0, priority=0, server='rmbp13.local.', properties={})
2017-09-27 21:43:26,036 INFO Login result: Accepted
```

Get current preset:
```python
In [4]: client.current_eq
Out[4]:
{'DeviceProfile': {'internalSpeaker': {'0': 1.846993446350098,
   '1': 1.856241226196289,
   '10': 0.8442622423171997,
   '11': 0.6557376980781555,
   '12': 0.2841529846191406,
   '13': -0.437158465385437,
   '14': -1.129325985908508,
   '15': -1.092895984649658,
   '16': -1.020036220550537,
   '17': -0.9836063385009766,
   '18': -0.4371582567691803,
   '19': 0.6557378768920898,
   '2': 1.863387227058411,
   '20': 1.202185988426208,
   '21': 1.329690456390381,
   '22': 1.584699511528015,
   '23': 1.712203979492188,
   '24': 1.85792350769043,
   '25': 2.149362564086914,
   '26': 2.295081853866577,
   '27': 2.349726676940918,
   '28': 2.4590163230896,
   '29': 2.51366114616394,
   '3': 1.867858290672302,
   '30': 2.568305969238281,
   '31': 2.622950792312622,
   '4': 1.888524174690247,
   '5': 1.884638428688049,
   '6': 1.730874180793762,
   '7': 1.451990604400635,
   '8': 1.293260455131531,
   '9': 1.127868890762329}},
 'PresetDetails': {'0': 3.315116405487061,
  '1': 3.3515465259552,
  '10': 1.876138210296631,
  '11': 1.639344096183777,
  '12': 0.9471765756607056,
  '13': -0.437158465385437,
  '14': -1.129325985908508,
  '15': -1.092895984649658,
  '16': -1.020036220550537,
  '17': -0.9836063385009766,
  '18': -0.4371582567691803,
  '19': 0.6557378768920898,
  '2': 3.38797664642334,
  '20': 1.202185988426208,
  '21': 1.329690456390381,
  '22': 1.584699511528015,
  '23': 1.712203979492188,
  '24': 1.85792350769043,
  '25': 2.149362564086914,
  '26': 2.295081853866577,
  '27': 2.349726676940918,
  '28': 2.4590163230896,
  '29': 2.51366114616394,
  '3': 3.424406766891479,
  '30': 2.568305969238281,
  '31': 2.622950792312622,
  '4': 3.49726676940918,
  '5': 3.533696889877319,
  '6': 3.296902894973755,
  '7': 2.823314905166626,
  '8': 2.586520910263062,
  '9': 2.349726676940918},
 'PresetDisplayName': 'Classical',
 'PresetHistoryValues': {},
 'PresetName': 'Classical',
 'PresetType': 0,
 'PresetUsedCount': 12,
 'isNew': False,
 'isSystemSpecificPreset': False}
```

Show all preset names (`client.boom_status` has a ton of other useful data too):
```python
In [5]: [preset['PresetDisplayName'] for preset in client.boom_status['RemoteContextInfo']['PresetList']]
Out[5]:
['My MacBook Pro',
 "60's",
 'Acoustic',
 'Bass Boost',
 'Bass Rock',
 'Bass Rock Bose',
 'Classical',
 'Dubstep',
 'Electronic',
 'Flat',
 'Hip Hop',
 'House',
 'Jazz',
 'Loud',
 'Movie',
 'Music',
 'Party',
 'Pop',
 'Reggae',
 'Rock',
 'Soft',
 'Treble Boost',
 'Vocals']
```

Change EQ preset:
```python
In [6]: client.set_eq('Movie')
2017-09-27 19:31:10,330 INFO Setting preset to: Movie
```

Disconnect (little green light on Boom tray icon disappears):
```python
In [8]: del(client)
2017-09-27 19:33:26,489 INFO Closing connection
```

## Technical Details

The Boom remote communicates with the Boom service running on the Mac via
unencrypted TCP communication on a random TCP port. The remote app first
discovers the Boom service and port sending [Multicast_DNS](
https://en.wikipedia.org/wiki/Multicast_DNS). It looks for any services
of type `_boom2._tcp.local.` or `_boom3._tcp.local.`:
 
<img src="https://user-images.githubusercontent.com/1694586/30942004-3ecdfc0e-a3b6-11e7-8aa7-269724c39bd4.png" width="500">

The mDNS response will contain any services discovered with name, IP address,
port, and server name (~hostname). Once you know the address and port, you can
connect and send a string with `1.3-someclient\n`. This will prompt the Boom
server (Mac) to ask you to if you want to allow or disallow the connection:

<img src="https://user-images.githubusercontent.com/1694586/30942146-27d286fe-a3b7-11e7-8456-f653c41dd5c9.png" height="200">

Once the client is allowed, the server will send the current status of the
Boom server, including presets, current player playing status, etc. There's a
lot of information there.

Sending and receiving data is a little trickier. The Boom server appears to
respond to any request with qty2 4-byte little-endian integers. I'm not sure
what the first 4 bytes are, but the second 4 bytes seems to be the size of the
data it wants to send. We can use that to properly receive data, which is JSON
strings as bytes, and convert them to python dicts (and back later when
sending).

When sending data, you must send a little-endian unsigned `17`
(`\x11\x00\x00\x00`) before you can send data. Then when you send you data it
must be prefixed with a little-endian unsigned integer representing the length
of the data you want to send. This makes it easy to work with the data as
python objects and convert them to bytes when sending.

## Limitations

Because the server continually sends updates when connected, there's no real
TCP "conversation" or acknowledgement when sending data. Currently the client
doesn't verify data, but in the future there could be a separate thread
constantly watching the status updates which could be then checked that the
status has indeed changed.
