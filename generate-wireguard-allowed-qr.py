#!/usr/bin/env python3
"""Generated Allowed IPs for WireGuard by specifying an IPv4 exclusion list"""
from argparse import (Action, ArgumentParser)
from ipaddress import (collapse_addresses, ip_network, IPv4Address, IPv4Network)
from shutil import which
from subprocess import (CalledProcessError, PIPE, run)
from sys import (argv, exit, stderr, stdout)

DEFAULT_IP_VERSION = 4
IPV4_ALL_NET = '0.0.0.0/0'
IPV6_ALL_NET = '::0/0'
QR_ENCODE_COMMAND = ['qrencode', '-t', 'ansi']


def error(msg, is_fatal=False, exit_code=1):
    stderr.write('{}: {}\n'.format('FATAL' if is_fatal is True else 'ERROR', msg))
    if is_fatal is True:
        exit(exit_code)


def fatal(msg, exit_code=1):
    error(msg, is_fatal=True, exit_code=exit_code)


def output(msg):
    stdout.write('{}\n'.format(msg))


def ip_network_safe(value, strict=True, supported_ip_version=None, do_supernet=True):
    """Make an IPv4Network or IPv4Network list from address or address list

    Input
    =====
    value (None, str, IPv4Network, IPv4Address, list)
        A single or list of dotted quad address(es), IPv4 CIDR notation address(es) or None
        If None, return IPv4Network('0.0.0.0/0')
    strict (bool): CIDR notation must not have host bits set when creating IPv4Network
    do_supernet (bool): Perform supernet operation if value is list

    Return
    ======
    IPv4Network object

    Notes
    =====
    Exceptions are fatal and can not be caught

    """
    if value is None:
        raise ValueError('value must be address (str dotted quad/CIDR, IPv4Network) or list of addresses')

    if supported_ip_version is None:
        supported_ip_version = DEFAULT_IP_VERSION

    if not isinstance(value, (IPv4Address, IPv4Network, str, list)):
        fatal('{} invalid type for IPv4Network (type:{})'.format(value, type(value)))

    if isinstance(value, (list)):
        if do_supernet is False:
            return [ip_network_safe(val, strict=strict) for val in value]
        return supernet([ip_network_safe(val, strict=strict) for val in value])

    try:
        return ip_network(value, strict=strict)
    except ValueError as err:
        fatal('invalid IPv4 network in base_network_list ({}) with strict={}'.format(
            err, strict))
    except Exception as err:
        fatal('unexpected error creating network from {} ({})'.format(
            value, err))


def exclude_nets_to_include_nets(net_exclusion_list, base_net=None, strict=True):
    """Exclude a list of networks from a larger network"""
    if isinstance(net_exclusion_list, (list, set)) and not net_exclusion_list:
        return list(base_net)

    if base_net is None:
        base_net = IPV4_ALL_NET

    net_exclusion_list = ip_network_safe(net_exclusion_list, strict=strict)

    base_net = ip_network_safe(base_net, strict=strict)
    allowed_ip_list = [base_net]

    for net_exclude in net_exclusion_list:
        running_allowed_netlist = []
        for working_allowed_ip in allowed_ip_list:
            if working_allowed_ip.overlaps(net_exclude):
                running_allowed_netlist.extend(working_allowed_ip.address_exclude(net_exclude))
                continue
            running_allowed_netlist.append(working_allowed_ip)
        allowed_ip_list = running_allowed_netlist
    return supernet(allowed_ip_list)


def supernet(network_list, strict=False):
    """Supernet list of addresses/networks

    network_list (list): List of addresses as dotted-quad str, CIDR str, IPv4Address
                         or IPv4Network

    Strict is set to False by default, this turns off the logic internal to
    ip_network that will cause an Exception to be raised if the host bits of
    the network are set
    """
    assert isinstance(network_list, list)
    supernetwork_list = list(collapse_addresses(
        [ip_network(net, strict=strict) for net in network_list]))
    return supernetwork_list


class CSVNetworkList(Action):
    """Validate strings and convert to IPv4Network objects as they're parsed"""

    def __call__(self, parser, namespace, values, option_string=None):
        for net in values:
            self._validate_network(parser, net)
        setattr(
            namespace,
            self.dest,
            list(map(ip_network, values))
        )

    def _validate_network(self, parser, net, ip_version=None):
        if ip_version is None:
            ip_version = DEFAULT_IP_VERSION
        try:
            network = ip_network(net)
            if network.version != ip_version:
                print(network.version)
                parser.error('Only IPv4 is supported. To add IPv6 support '
                             'yourself, start by changing references to IPV4_ALL_NET')
            return network
        except ValueError:
            error('BAD ADDRESS: Invalid network in list: {}'.format(net))
            if '/' in net:
                parser.error('Ensure that no host bits are set in CIDR notation'
                             'network addresses, or use "--loose"')
            parser.error('Ensure you only provide valid IPv4 addresses or CIDR '
                         'notation networks separated by spaces')


def cli(appname):
    """Simple CLI argument parsing"""
    argparser = ArgumentParser(prog=appname)
    argparser.add_argument(
        '--exclude',
        action=CSVNetworkList,
        dest='excluded_network_list',
        nargs='+',
        required=True,
        help='List of networks and IP addresses separated by commas for exclusion',
        metavar='n.n.n.n[/mask]')
    argparser.add_argument(
        '--loose',
        action='store_false',
        dest='strict',
        required=False,
        default=True,
        help='Specify strict CIDR block definitions, fail when the host bit is '
             'set in a CIDR block')
    argparser.add_argument(
        '-D', '--debug',
        action='store_true',
        dest='debug',
        required=False,
        default=False,
        help='Enable debug messages')
    argparser.add_argument(
        '-q', '--qrencode',
        dest='qrencode',
        action='store_true',
        required=False,
        default=False,
        help='Output a QR code to the screen using ANSI escape chars')
    argparser.add_argument(
        '-l', '--lines-output',
        dest='enable_lines',
        action='store_true',
        default=False,
        required=False,
        help='Produce output in line-based format')
    argparser.add_argument(
        '-4', '--no-ip6',
        dest='no_ip6',
        action='store_true',
        default=False,
        required=False,
        help='Do not include {} output'.format(IPV6_ALL_NET))
    argparser.add_argument(
        '-W', '--no-wireguard-format',
        dest='wireguard_format',
        action='store_false',
        default=True,
        required=False,
        help='Exclude the "AllowedIPs = " literal')
    argparser.add_argument(
        '-C', '--no-csv-output',
        dest='disable_csv',
        action='store_true',
        default=False,
        required=False,
        help='Disable output of single-line CSV (WireGuard-style) format')

    args = argparser.parse_args()

    if args.qrencode is True:
        qr_command = QR_ENCODE_COMMAND[0]
        args.qrencode_path = which(qr_command)
        if args.qrencode_path is None:
            argparser.error('Application "{}" not in path, try apt-get '
                            'install qrencode'.format(qr_command))

    return argparser.parse_args()


def main():
    """Get command-line arguments and output results in specified formats"""
    args = cli(argv[0])
    excluded_network_list = args.excluded_network_list
    inclusive_netlist = exclude_nets_to_include_nets(excluded_network_list, strict=args.strict)

    if args.no_ip6 is False:
        inclusive_netlist.append(ip_network_safe(IPV6_ALL_NET))

    csv_inclusive_netlist = ','.join(
        [included_net.compressed for included_net in inclusive_netlist])

    if args.qrencode is True:
        qr_encode_command = QR_ENCODE_COMMAND + [csv_inclusive_netlist]
        output('Generating WireGuard friendly QR code format:')
        try:
            result = run(qr_encode_command, stdout=PIPE, check=True)
        except CalledProcessError as err:
            fatal('failed to invoke `qrencode` app ({})'.format(err))
        output(result.stdout.decode('utf-8'))
        output('')

    if args.enable_lines:
        output('Line-based output:')
        for included_net in [net.compressed for net in inclusive_netlist]:
            output('{}'.format(included_net))

    if args.disable_csv is False:
        output('-- CSV line output --')
        output('{}{}'.format(
            'AllowedIPs = ' if args.wireguard_format is True else '',
            csv_inclusive_netlist))


if __name__ == '__main__':
    main()
