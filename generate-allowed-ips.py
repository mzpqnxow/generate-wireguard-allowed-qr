#!/usr/bin/env python3
"""Generated Allowed IPs for WireGuard, see README.md for more details"""
from argparse import (
    Action,
    ArgumentParser)
from copy import copy
from ipaddress import (
    collapse_addresses,
    ip_network,
    IPv4Address,
    IPv4Network)
from shutil import which
from subprocess import (
    CalledProcessError,
    PIPE,
    run)
from sys import (
    argv,
    stderr,
    stdout)

SUPPORTED_IP_VERSION = 4
IPV4_ANY_NET = '0.0.0.0/0'
QR_ENCODE_COMMAND = ['qrencode', '-t', 'ansi']
G_DEBUG = False


def error(msg, fatal=False, exit_code=1):
    stderr.write('{}: {}\n'.format('FATAL' if fatal is True else 'ERROR', msg))
    if fatal is True:
        exit(exit_code)


def fatal(msg, exit_code=1):
    error(msg, fatal=True, exit_code=exit_code)


def debug(msg):
    global G_DEBUG
    if G_DEBUG is False:
        return
    stderr.write('DEBUG: {}\n'.format(msg))


def output(msg):
    stdout.write('{}\n'.format(msg))


def ip_network_safe(value, strict=True):
    """Make an IPv4Network, handling exceptions and special cases

    Input
    =====
    value (None, str, IPv4Network, IPv4Address): A dotted quad address, IPv4 CIDR notation
                                                 address, or None. If None, return 0/0
    strict (bool): CIDR notation must not have host bits set when creating IPv4Network

    Return
    ======
    IPv4Network object

    Notes
    =====
    Exceptions are fatal and can not be caught


    """
    if value is None:
        return ip_network(IPV4_ANY_NET)

    if not isinstance(value, (IPv4Address, IPv4Network, str)):
        fatal('{} invalid type for IPv4Network (type:{})'.format(value, type(value)))

    try:
        return ip_network(value, strict=strict)
    except ValueError as err:
        fatal('invalid IPv4 network in base_network_list ({}) with strict={}'.format(
            err, strict))
    except Exception as err:
        fatal('unexpected error creating network from {} ({})'.format(
            value, err))


def ip_network_list_safe(values, supernet=True, strict=True):
    """Return a list of IPv4Network objects

    See ip_network_safe for documentation, this is just a wrapper

    Set supernet=True to supernet the list

    """
    if supernet is False:
        return [ip_network_safe(value, strict=strict) for value in values]
    return supernet_list([ip_network_safe(value, strict=strict) for value in values])


def exclude_net_from_net(exclude_net, base_network, strict=True):
    assert isinstance(exclude_net, (str, IPv4Network))
    assert isinstance(base_network, (str, IPv4Network))

    exclude_net = ip_network_safe(exclude_net, strict=strict)
    base_network = ip_network_safe(base_network, strict=strict)

    try:
        network_list = list(base_network.address_exclude(exclude_net))
        return list(network_list)
    except ValueError as err:
        print(err)
    return [base_network]


def exclude_net_from_net_list(exclude_net, base_network_list, strict=True):
    """Useful for exception handling"""
    exclude_net = ip_network_safe(exclude_net, strict=strict)
    base_network_list = ip_network_list_safe(base_network_list, strict=strict)

    looping_base_list = copy(base_network_list)
    running_include_list = list()
    for base_net in looping_base_list:
        try:
            running_include_list.extend(list(base_net.address_exclude(exclude_net)))
        except ValueError:
            # Because of the type checking, ValueError should be harmless
            debug('{} not a part of {}, skipping'.format(exclude_net, base_net))
            running_include_list.append(base_net)
        except Exception as err:
            fatal('unexpected error ({})'.format(err))

    return running_include_list


def exclude_net_list(net_exclusion_list, base_net=None, strict=True):
    """Exclude a list of networks from a larger network"""
    if isinstance(net_exclusion_list, (list, set)) and not net_exclusion_list:
        return list(base_net)

    net_exclusion_list = ip_network_list_safe(net_exclusion_list, strict=strict)

    base_net = ip_network_safe(base_net, strict=strict)

    first_exclusion = ip_network_safe(net_exclusion_list.pop(), strict=strict)
    running_list = exclude_net_from_net(first_exclusion, base_net, strict=strict)

    for exclude_net in net_exclusion_list:
        running_list = exclude_net_from_net_list(
            ip_network_safe(exclude_net, strict=strict),
            running_list)
        running_list = list(running_list)

    return running_list


def supernet_list(network_list, strict=False):
    """Supernet a list of ASCII or ipaddress.ip_network objects

    Because ip_network works fine on both ASCII and ip_network objects,
    network_list can be a mixed set of both str and IPV4Networks. It is
    redundant to use ip_network on an IPv4Nework, but it simplifies the logic

    Strict is set to False by default, this turns off the logic internal to
    ip_network that will cause an Exception to be raised if the host bits of
    the network are set
    """
    assert isinstance(network_list, (list, set))
    return list(collapse_addresses(
        [ip_network(net, strict=strict) for net in network_list]))


class CSVNetworkList(Action):
    """Validate and convert addresses dynamically via ArgumentParser"""

    def __call__(self, parser, namespace, values, option_string=None):
        # ascii_net_list = values.split(',')
        for net in values:
            self._validate_network(parser, net)
        setattr(
            namespace,
            self.dest,
            list(map(ip_network, values))
        )

    def _validate_network(self, parser, net):
        try:
            network = ip_network(net)
            if network.version != SUPPORTED_IP_VERSION:
                parser.error('Only IPv4 is supported. To add IPv6 support '
                             'yourself, start by changing ALL_ADDRESS')
            return network
        except ValueError:
            print()
            print('BAD ADDRESS: Invalid network in list: {}'.format(net))
            print()
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
        dest='lines',
        action='store_true',
        default=False,
        required=False,
        help='Produce output in line-based format')
    argparser.add_argument(
        '-4', '--include-ip4-only',
        dest='ip4_only',
        action='store_true',
        default=False,
        required=False,
        help='Do not include ::0/0 in AllowedIPs output')
    argparser.add_argument(
        '-C', '--no-csv-output',
        dest='disable_csv',
        action='store_true',
        default=False,
        required=False,
        help='Disable output of single-line CSV')

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
    # Too lazy to use Python logging
    global G_DEBUG
    args = cli(argv[0])
    G_DEBUG = args.debug

    excluded_network_list = args.excluded_network_list
    inclusive_netlist = exclude_net_list(excluded_network_list, strict=args.strict)

    csv_inclusive_netlist = ','.join(
        [included_net.compressed for included_net in inclusive_netlist])

    if args.qrencode is True:
        qr_encode_command = QR_ENCODE_COMMAND + [csv_inclusive_netlist]
        debug('Generating WireGuard friendly QR code format:')
        try:
            result = run(qr_encode_command, stdout=PIPE, check=True)
        except CalledProcessError as err:
            fatal('failed to invoke `qrencode` app ({})'.format(err))
        output(result.stdout.decode('utf-8'))
        output('')

    if args.lines:
        debug('Line-based output:')
        for included_net in [net.compressed for net in inclusive_netlist]:
            output('{}'.format(included_net))

    if args.disable_csv is False:
        debug('CSV line output:')
        output('AllowedIPs = {}{}'.format(
            csv_inclusive_netlist, ',::0/0' if args.ip4_only is False else ''))


if __name__ == '__main__':
    main()
