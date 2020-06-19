# wireguard-exclusions-qr

Given a list of excluded IPv4 addresses (dotted quad, CIDR) print an inclusion list suitable for the [WireGuard](https://www.wireguard.com/) mobile app

## About

This script is intended for use with [WireGuard](https://www.wireguard.com) clients, specifically the mobile app. You can specify an inclusion list, instruction the WireGuard client which addresses should transit the tunnel. Additionally, there is an option for all private addresses to *not* use the tunnel. However, there is no simple way to specify exclusion of specific networks. To do so, you must provide the inverse, which is a list of networks to be routed through the tunnel. In some cases, you may want only a few specific LAN addresses to be excluded from the WireGuard tunnel, and may not be able to do this on the peer. For example, you may be using a WireGuard peer that you do not have adminstrator access to, such as a third party VPN provided by a friend, free service or commercial service.

## Caveat Emptor

YMMV. Depending on the client device and the WireGuard app version, you may need to explicitly include or exclude the Internet gateway of the device or the tunnel itself. Feedback is welcome, this is an experimental script. See also the TODO section ...

## Usage

Given a list of dotted-quad and CIDR notation IPv4 networks, generate the inverse in the format WireGuard prefers

This was written to create an "Allowed IPs" list for the WireGuard mobile app. WireGuard currently doesn't allow you to supply an "Excluded IPs" option, so you have to invert the networks that you want to bypass the tunnel. This overengineered app will do that for you. One very convenient feature is printing a QR code so that the Allowed IPs list will be easy to copy to a mobile device

QR code generation currently depends on the `qrencode` command-line tool:

```
$ sudo apt-get install qrencode
```

## Help Output

```
usage: ./allowed-ips.py [-h] --exclude n.n.n.n[/mask] [n.n.n.n[/mask] ...]
                        [--loose] [-D] [-q] [-l] [-C]

optional arguments:
  -h, --help            show this help message and exit
  --exclude n.n.n.n[/mask] [n.n.n.n[/mask] ...]
                        List of networks and IP addresses separated by commas
                        for exclusion
  --loose               Specify strict CIDR block definitions, fail when the
                        host bit is set in a CIDR block
  -D, --debug           Enable debug messages
  -q, --qrencode        Output a QR code to the screen using ANSI escape chars
  -l, --lines-output    Produce output in line-based format
  -C, --no-csv-output   Disable output of single-line CSV
```

## Examples

Use WireGuard tunnel for all networks except 192.168.1.0/24 and 192.168.2.0/24:

```
$ ./allowed-ips.py --exclude 192.168.1.0/24 192.168.2.0/24
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.3.0/24,
192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,192.169.0.0/16,
192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,200.0.0.0/5,
208.0.0.0/4,224.0.0.0/3,::0/0
```

The same, but don't route IPv6 through the tunnel (note the last network in the output):

```
$ ./allowed-ips.py -4 --exclude 192.168.1.0/24 192.168.2.0/24
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.3.0/24,
192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,192.169.0.0/16,
192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,200.0.0.0/5,
208.0.0.0/4,224.0.0.0/3
```

Allow only 192.168.1.1 and 192.168.1.2 to bypass the tunnel:

```
$ ./allowed-ips.py --exclude 192.168.1.1 192.168.1.2
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.1.0/32,
192.168.1.3/32,192.168.1.4/30,192.168.1.8/29,192.168.1.16/28,192.168.1.32/27,192.168.1.64/26,192.168.1.128/25,
192.168.2.0/23,192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,
192.169.0.0/16,192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,
200.0.0.0/5,208.0.0.0/4,224.0.0.0/3,::0/0
```

The same, but also generate a QR code on the terminal that can be scanned by a mobile device:

```
$ ./allowed-ips.py --no-csv --qr --exclude 192.168.1.1 192.168.1.2
...
<ANSI QR CODE>
...
```

**NOTE**: When using QR code, the 'AllowedIPs =' string literal will not be included

## QR Code Support

No Python QR libraries are used by this app, it depends on the `qrencode` app that is commonly available in most Linux distributions. On Debian-based distros. This app can be installed using:

```
$ sudo apt-get install qrencode
```

If you would like to use a different QR code generator, you can change the `QR_ENCODE_COMMAND` list in the script. However, you will need to know what you're doing

## TODO

I would like to do this in Python, but this will require two third-party packages as
far as I can tell, probably these (or similar):

  1. climage (https://pypi.org/project/climage/)
  2. qrcode (https://pypi.org/project/qrcode/)

This has not been exhaustively tested and this comes with no guarantees. You can spot-check the generated list using the `spotcheck-allowed-ips.py` script included in this repository

## Copyright

(C) 2020, copyright@mzpqnxow.com, BSD 3-Clause License
Please see COPYING file