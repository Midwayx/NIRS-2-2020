from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime
import pygal
from os import getcwd


class BasicClass:

    def __init__(self, host, port, community):
        self.host = host
        self.port = port
        self.community = community
        self.cmd = cmdgen.CommandGenerator()

    def snmp_get_request(self, oid):

        response = self.cmd.getCmd(cmdgen.CommunityData(self.community),
                                   cmdgen.UdpTransportTarget((self.host, self.port)),
                                   oid)
        value = response[3][0]
        return str(value).split('= ')[1]

    def snmp_set_request(self, oid, value):

        errorIndication, errorStatus, errorIndex, varBinds = self.cmd.setCmd(
            cmdgen.CommunityData(self.community),
            cmdgen.UdpTransportTarget((self.host, self.port)), (oid, value))
        # Check for errors and print out results
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print('%s at %s' % (
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1] or '?'
                )
                      )
            else:
                for name, val in varBinds:
                    print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

    def if_data(self, data, file='/home/results_1.txt'):
        out_data = {}
        for interface in range(1, 25):
            out_data.update({f'{interface}_'+name: self.snmp_get_request(f'{oid}' + str(interface)) for
                             name, oid in data.items()})
        out_data['Time'] = datetime.datetime.utcnow().isoformat()
        with open(file, 'a') as f:
            f.write(str(out_data))
            f.write('\n')

    def plot_pygal_graph(self, iface, file='/home/results_1.txt'):
        self.x_time = []
        self.out_packets = []
        self.out_octets = []
        self.in_packets = []
        self.in_octets = []

        with open(file, 'r') as f:
            for line in f.readlines():
                line = eval(line)
                self.x_time.append(str(line['Time']))
                self.out_packets.append(float(line[f'{iface}_out_uPackets']))
                self.out_octets.append(float(line[f'{iface}_out_oct']))
                self.in_packets.append(float(line[f'{iface}_in_uPackets']))
                self.in_octets.append(float(line[f'{iface}_in_oct']))

        line_chart = pygal.Line()
        line_chart.title = f"Interface {iface}"
        line_chart.x_labels = self.x_time
        line_chart.add('out_octets', self.out_octets)
        line_chart.add('out_packets', self.out_packets)
        line_chart.add('in_octets', self.in_octets)
        line_chart.add('in_packets', self.in_packets)
        line_chart.render_to_file(f'if_statistic_{iface}.svg')

    def if_search(self, data, if_num=None, if_range=None, up_only=False):
        output = {}
        if if_range is not None:
            for interface in range(if_range[0], if_range[1]):
                out_data = {name: self.snmp_get_request(f'{oid}'+str(interface)) for name, oid in data.items()}
                if up_only:
                    if int(out_data['OperStatus']) == 1:
                        output[interface] = out_data
                else:
                    output[interface] = out_data
        elif if_num:
            output[int(if_num)] = {name: self.snmp_get_request(f'{oid}'+str(if_num)) for name, oid in data.items()}

        self.__if_status(output)

    def __if_status(self, data):
        for interface in data:
            print("\n{}\n*{:^58}*\n{}\n".format('*' * 60, f'Interface number: {interface}', '*' * 60))

            out_data = data[interface]
            descr = out_data['Descr']
            print(f'description: {descr}')

            status = int(out_data['OperStatus'])
            if status == 1:
                print('interface status: up')
            elif status == 2:
                print('interface status: down')
            else:
                print('interface status: unknown')

            speed = int(out_data['Speed'])
            if speed == 10**9:
                print('speed rate: 1 Gb/s')
            elif speed == 10**8:
                print('speed rate: 100 Mb/s')
            elif speed == 10**7:
                print('speed rate: 10 Mb/s')
            else:
                print(f'speed rate: {speed} bits/s')

            duplex = int(out_data['Duplex'])
            if duplex == 1:
                print('duplex: unknown (interface is down)')
            if duplex == 2:
                print('duplex: half duplex')
            if duplex == 3:
                print('duplex: full duplex')

            mac = out_data['Mac address'].split('0x')[1].zfill(12)
            mac = ':'.join([mac[i:i + 2] for i in range(0, 12, 2)])
            print(f'mac address: {mac.upper()}')


datas = {
          'in_oct': '1.3.6.1.2.1.2.2.1.10.', 'in_uPackets': '1.3.6.1.2.1.2.2.1.11.',
          'out_oct': '1.3.6.1.2.1.2.2.1.16.', 'out_uPackets': '1.3.6.1.2.1.2.2.1.17.',
         }

status_data = {
                'Mac address': '1.3.6.1.2.1.2.2.1.6.',
                'Speed': '1.3.6.1.2.1.2.2.1.5.',
                'Descr': '1.3.6.1.2.1.2.2.1.2.',
                'OperStatus': '1.3.6.1.2.1.2.2.1.8.',
                'Duplex': '1.3.6.1.2.1.10.7.2.1.19.'
                }

flag = False
if __name__ == '__main__':
    snmp = BasicClass('127.0.0.1', 8980, 'dlink-dgs3100')
    ans = ''
    while ans not in ['quit', 'exit', 'bye']:
        print('\navailable command:\n1 - show interface status\n2 - show port statistics'
              '\n3 - update statistics log\n[quit | exit | bye] for exit')
        ans = input('\nPlease input command: ')
        if str(ans) == '1':
            helps = True
            while 1:
                print('\nYou in show interface mod')
                if helps:
                    print('possible input: '
                          '\n[num] for show interface by number from [1:25]'
                          '\n[start_num:end_num] [OPTIONAl add: :up] for show interfaces in this range '
                          '(optional only upped) (max: 1:25)'
                          '\n[back] for return'
                          '\n[exit | quit] for exit')
                select = input()
                try:
                    if_num = int(select)
                    if 0 < if_num < 25:
                        snmp.if_search(status_data, if_num=if_num)
                        helps = False
                        continue
                    else:
                        print('Unrecognized number! Use num from [1:24]')
                        helps = True
                        continue
                except ValueError:
                    pass

                if len(select.split(':')) == 2 or len(select.split(':')) == 3:
                    inp = [str(i).strip() for i in select.split(':')]
                    try:
                        start = int(inp[0])
                        end = int(inp[1])
                        if end - start < 0 or start <= 0 or start > 24 or end > 25:
                            print('Invalid input. Please, try again')
                            helps = True
                            continue
                        elif len(inp) == 3:
                            if inp[2] == 'up':
                                snmp.if_search(status_data, if_range=(start, end), up_only=True)
                                helps = False
                                continue
                            else:
                                print('Invalid input. Please, try again')
                                helps = True
                                continue
                        else:
                            snmp.if_search(status_data, if_range=(start, end))
                            helps = False
                            continue

                    except ValueError:
                        print('Invalid input. Please, try again')
                        helps = True
                        continue
                elif select == 'back':
                    break
                elif select in ['quit', 'exit', 'bye']:
                    exit(0)
                else:
                    print('Invalid input. Please, try again')
                    helps = True
                    continue
        elif str(ans) == '2':
            helps = True
            while 1:
                print('\nYou in show port statistics mod')
                if helps:
                    print('possible input: '
                          '\n[num] for show port statistics by number from [1:25]'
                          '\n[back] for return'
                          '\n[exit | quit] for exit')
                select = input()
                try:
                    if_num = int(select)
                    if 0 < if_num < 25:
                        snmp.if_data(datas)
                        snmp.plot_pygal_graph(str(if_num))
                        helps = False
                        print(f'Success! Open {getcwd()}/if_statistic_{if_num}.svg for see info.'
                              f'\nNote: Use Web-browser for better experience.')
                        continue
                    else:
                        print('Unrecognized number! Use num from [1:24]')
                        helps = True
                        continue
                except ValueError:
                    pass
                if select == 'back':
                    break
                elif select in ['quit', 'exit', 'bye']:
                    exit(0)
        elif str(ans) == '3':
            snmp.if_data(datas)
            print('\nStatistics log successfully updated!')
            continue
        else:
            print('Invalid input. Please, try again')
            helps = True
            continue

    if flag:
        snmp.if_data(datas)

