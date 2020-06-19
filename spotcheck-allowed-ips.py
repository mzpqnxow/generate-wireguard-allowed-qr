#!/usr/bin/env python3
"""
Short script to check membership/overlap of a single IPv4 network address in a list of networks

Useful to spotcheck output from generate-allowed-ips.py

in a list of network addresses (dotted quad or CIDR)

Usage:
    spotcheck-inclusion.py <n.n.n.n[/x]> <n.n.n.n[/x]>[,<n.n.n.n[/x]]

Example:
    $ check.py 192.168.1.1 0.0.0.0/1,128.0.0.0/2,192.0.0.0/9,192.128.0.0/11,192.160.0.0/13,192.168.0.0/24,192.168.1.0/32,\
      >192.168.1.3/32,192.168.1.4/30,192.168.1.8/29,192.168.1.16/28,192.168.1.32/27,192.168.1.64/26,\
      >192.168.1.128/25,192.168.2.0/23,192.168.4.0/22,192.168.8.0/21,192.168.16.0/20,192.168.32.0/19,\
      >192.168.64.0/18,192.168.128.0/17,192.169.0.0/16,192.170.0.0/15,192.172.0.0/14,192.176.0.0/12,\
      >192.192.0.0/10,193.0.0.0/8,194.0.0.0/7,196.0.0.0/6,200.0.0.0/5,208.0.0.0/4,224.0.0.0/3

"""
from ipaddress import (ip_address, ip_network)
from sys import (argv, exit)


def address_in_networks(check_network_address, network_address_list):
    assert isinstance(network_address_list, (list, set))
    network_address_list = to_network(network_address_list)
    check_network_address = to_network(check_network_address)
    for network_address in network_address_list:
        if check_network_address in network_address:
            return network_address
    return False


def to_network(value, strict=False):
    """Handle exceptions while converting an address to Python ipaddress.IPv4Network via ip_network"""
    try:
        if isinstance(value, (list, set)):
            return list([ip_network(addr, strict=strict) for addr in value])
        return ip_address(value)
    except ValueError as err:
        print('Invalid type for network address or network address list!')
        print('ERROR: {}'.format(err.args[0]))
        exit(1)
    except Exception as err:
        print('General error, invalid input')
        print(err)
        exit(1)


def main():
    if len(argv) != 3:
        print('Usage: {} <address> <address1>[,address2][,address3]'.format(argv[0]))
        print('Any of the address values may be a dotted quad or CIDR notation IPv4 address')
        exit(1)

    test_addr = argv[1]
    addr_list = argv[2].split(',')
    result = address_in_networks(test_addr, addr_list)

    if result is False:
        print('Found no match!\n')
        print('{} does not appear to be a part of any of the following:\n'.format(test_addr))
        for addr in addr_list:
            print('  - {}'.format(addr))
        exit(1)

    print('Found a match/overlap!')
    print('  - {} is a part of/overlaps with {}'.format(test_addr, result.compressed))


if __name__ == '__main__':
    main()
