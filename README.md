# generate-wireguard-allowed-qr

Given a list of IPv4 addresses (dotted quad, CIDR) print an inclusion list suitable for the [WireGuard](https://www.wireguard.com/) mobile app, optionally generating a QR code. Useful for excluding only a partial set of LAN (or WAN) addresses from the WireGuard tunnel. Currently, the only "easy" option for accessing a LAN is to opt *all* RFC1918/RFC3330 private addresses out of the tunnel, using the checkbox that the WireGuard client provides. This script allows a more granular specification, and also allows the specification of specific WAN addresses as well

## Specific Use-Case (LAN + Security Concerns)

Consider a mobile user with an on-demand WireGuard VPN connection for purposes of both privacy as well as reduction of attack surface/security of the client device. The WireGuard peer is on the public Internet, protecting the users' first-hop/ISP from mining and selling their browsing habits. However, this user wants to access some specific hosts on the LAN directly

One existing (and easy) solution is to use the built-in "Exclude Private IPs" option in the WireGuard mobile app. However, this is not granular and will bypass the tunnel for *all* RFC1918/RFC3330 networks. Using this rinky-dink little app, you can specify granular exclusions, e.g. `192.168.1.2 192.168.1.3 192.168.1.4` for the WireGuard tunnel

This sort of configuration has two functions:

1. Protects part of the LAN in the event the mobile device is compromised or exploited with some goofy CSRF bug
2. Protects the device itself from potentially "rogue" LAN devices

Allowing only 192.168.1.2, 192.168.1.3 and 192.168.1.4 effectively protects the rest of the 192.168.1.0/24 network from being exposed to the device. It also effectively protects the device from the rest of the LAN

## Why is such involved code required to generate a list of networks?

WireGuard mobile only allows the client to specify IP addresses that are "allowed" to use the tunnel. It does not allow specify in the other direction. Because of this, you can't briefly or easily say "all traffic except to/from host 192.168.1.3 should transit the tunnel easily". Instead, you need a list of CIDR notation networks that make up the entire IPv4 address space, excluding "192.168.1.3". If you're curious, this value is:

```
0.0.0.0/1,128.0.0.0/2,224.0.0.0/3,208.0.0.0/4,200.0.0.0/5,196.0.0.0/6,194.0.0.0/7,193.0.0.0/8,192.0.0.0/9,192.192.0.0/10,192.128.0.0/11,192.176.0.0/12,192.160.0.0/13,192.172.0.0/14,192.170.0.0/15,192.169.0.0/16,192.168.128.0/17,192.168.64.0/18,192.168.32.0/19,192.168.16.0/20,192.168.8.0/21,192.168.4.0/22,192.168.2.0/23,192.168.0.0/24,192.168.1.128/25,192.168.1.64/26,192.168.1.32/27,192.168.1.16/28,192.168.1.8/29,192.168.1.4/30,192.168.1.0/31,192.168.1.2/32,::0/0,::0/0
```

A bit much to effectively specify a single host... and not so simple to construct in your head, unless you're an advanced human subnet calculator


## Sad Things

 * This code could be written much more succinctly, feel free to strip it down
 * If/when the a `Disallowed IPs` option is provided in the WireGuard client, to complement/provide and alternative to the `Allowed IPs` option, this script will become 100% worthless :>

## Caveat Emptor

YMMV. Depending on the client device and the WireGuard app version, you may need to explicitly include or exclude the Internet gateway of the device or the tunnel itself. This was only written and tested for a single (simple) scenario

Feedback is welcome, this is an experimental script. See also the TODO section ...

## Usage

Given a list of dotted-quad and CIDR notation IPv4 networks, generate the inverse in the format WireGuard prefers

This was written to create an "Allowed IPs" list for the WireGuard mobile app. WireGuard currently doesn't allow you to supply an "Excluded IPs" option, so you have to invert the networks that you want to bypass the tunnel. This overengineered app will do that for you. One very convenient feature is printing a QR code so that the Allowed IPs list will be easy to copy to a mobile device

QR code generation currently depends on the `qrencode` command-line tool:

```
$ sudo apt-get install qrencode
```

## Help Output

```
$ ./generate-wireguard-allowed-qr.py --help
usage: ./generate-wireguard-allowed-qr.py [-h] --exclude n.n.n.n[/mask]
                                          [n.n.n.n[/mask] ...] [--loose] [-D]
                                          [-q] [-l] [-4] [-W] [-C]

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
  -4, --no-ip6          Do not include ::0/0 output
  -W, --no-wireguard-format
                        Exclude the "AllowedIPs = " literal
  -C, --no-csv-output   Disable output of single-line CSV (WireGuard-style)
                        format
```

## Examples

Use WireGuard tunnel for all networks except 192.168.1.0/24 and 192.168.2.0/24:

```
$ ./generate-wireguard-allowed-qr.py --exclude 192.168.1.0/24 192.168.2.0/24
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.3.0/24,
192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,192.169.0.0/16,
192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,200.0.0.0/5,
208.0.0.0/4,224.0.0.0/3,::0/0
```

The same, but don't route IPv6 through the tunnel (note the last network in the output):

```
$ ./generate-wireguard-allowed-qr.py -4 --exclude 192.168.1.0/24 192.168.2.0/24
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.3.0/24,
192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,192.169.0.0/16,
192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,200.0.0.0/5,
208.0.0.0/4,224.0.0.0/3
```

Allow only 192.168.1.1 and 192.168.1.2 to bypass the tunnel:

```
$ ./generate-wireguard-allowed-qr.py --exclude 192.168.1.1 192.168.1.2
AllowedIPs = 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.1.0/32,
192.168.1.3/32,192.168.1.4/30,192.168.1.8/29,192.168.1.16/28,192.168.1.32/27,192.168.1.64/26,192.168.1.128/25,
192.168.2.0/23,192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,192.168.64.0/18,192.168.128.0/17,
192.169.0.0/16,192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,
200.0.0.0/5,208.0.0.0/4,224.0.0.0/3,::0/0
```

The same, but also generate a QR code on the terminal that can be scanned by a mobile device. Note that when using `--qr`, the `AllowedIPs =` literal will not be printed as it is not required on a mobile device

```
$ ./generate-wireguard-allowed-qr.py --no-csv-output --qr --exclude 192.168.1.1 192.168.1.2
...
<ANSI QR CODE>
...
```

**NOTE**: When using QR code, the 'AllowedIPs =' string literal will not be included
**IMPORTANT**: You may also need to specify the WireGuard peer address as an exclusion

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

This has not been exhaustively tested and this comes with no guarantees. You can spot-check the generated list using the `spotcheck-generate-wireguard-allowed-qr.py` script included in this repository

## Copyright

(C) 2020, copyright@mzpqnxow.com, BSD 3-Clause License
Please see COPYING file