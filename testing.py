import os
import argparse
#import faker
import socket


def parse_args():
    # set detault balues for the optional arguments
    hostname = socket.gethostname()
    localhost_ip = socket.gethostbyname(hostname)

    parser = argparse.ArgumentParser(description="simulate SNMP devices")
    parser.add_argument('-d', "--no_of_devices", type=int, help="number of snmp devices")
    args = parser.parse_args()
    return args


def create_snmp(**kwargs):
    num_devices = kwargs.get('no_of_devices')
    #fakerq = faker.Faker()
    port_list = []
    for i in range(num_devices):
        try:
            port = get_open_port(host="127.0.0.1")
            port_list.append(port)
            os.system("snmpsimd.py --daemonize --process-user=nobody --process-group=nogroup --data-dir=/home/midway/data --agent-udpv4-endpoint=127.0.0.1:%s" % port)
        except:
            raise ValueError("error in running the snmp device 'snmpsimd.py' command")

    #ip_list = [fakerq.ipv4() for port in port_list]
    #update_iptables(port_list, ip_list)

    return port_list


def get_open_port(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()

    return port


def update_iptables(port_list, ip_list):
    for port, ip in zip(port_list, ip_list):
        try:
            os.system(
                "sudo iptables -t nat -A OUTPUT -p udp -d %s --dport 1:65535 -j DNAT --to-destination 127.0.0.1:%s" % (
                ip, port))
            os.system(
                "sudo iptables -t nat -A OUTPUT -p icmp -d %s  --icmp-type echo-request -j DNAT --to-destination 127.0.0.1:%s" % (
                ip, port))
            os.system(
                "sudo iptables -t nat -A OUTPUT -p tcp -d %s  --dport 22 -j DNAT --to-destination 127.0.0.1:%s" % (
                ip, port))
        except OSError:
            raise ValueError('error in running the iptable update commands')


if __name__ == "__main__":
    args = parse_args()
    print("Creating SNMP simulated devices................")
    port_list = create_snmp(no_of_devices=args.no_of_devices)
    print("snmp devices are being run on these ports:", port_list)