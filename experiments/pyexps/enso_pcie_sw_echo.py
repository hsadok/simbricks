# Copyright (c) 2021-2024, Max Planck Institute for Software Systems,
# National University of Singapore, and Carnegie Mellon University
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
Experiment, which simulates two hosts with Enso one running an echo server and
the other EnsoGen.

Both hosts also contain a PCI switch to connect multiple NICs to the host.
"""

import typing as tp

import simbricks.orchestration.experiments as exp
import simbricks.orchestration.nodeconfig as node
import simbricks.orchestration.simulators as sim


class EnsoLocal(node.EnsoNode):

    def __init__(self):
        super().__init__()
        self.local_enso_dir = None

        # Uncomment to specify a local Enso directory to copy to the node.
        # self.local_enso_dir = "/enso"


class ConfiguredEnsoGen(node.EnsoGen):

    def __init__(self):
        super().__init__()
        self.count = 1000  # Number of packets to send.


def create_basic_hosts_with_pcie_switch(
    e: exp.Experiment,
    num: int,
    name_prefix: str,
    net: sim.NetSim,
    nic_class: tp.Type[sim.NICSim],
    pci_switch_class: tp.Type[sim.PCISwitchSim],
    host_class: tp.Type[sim.HostSim],
    nc_class: tp.Type[node.NodeConfig],
    app_class: tp.Type[node.AppConfig],
    ip_start: int = 1,
    ip_prefix: int = 24
) -> tp.List[sim.HostSim]:
    """
    Creates and configures multiple hosts to be simulated using the given
    parameters.

    Args:
        num: number of hosts to create
    """

    hosts: tp.List[sim.HostSim] = []
    for i in range(0, num):
        nic = nic_class()
        nic.set_network(net)
        nic.name = 'enso_nic'

        nic2 = sim.I40eNIC()
        nic2.set_network(net)
        nic2.name = 'i40e_nic'

        node_config = nc_class()
        node_config.prefix = ip_prefix
        ip = ip_start + i
        node_config.ip = f'10.0.{int(ip / 256)}.{ip % 256}'
        node_config.app = app_class()

        host = host_class(node_config)
        host.name = f'{name_prefix}.{i}'

        pci_sw = pci_switch_class()
        pci_sw.name = f'{name_prefix}.{i}.pci_sw'

        pci_sw.add_nic(nic)
        pci_sw.add_nic(nic2)

        host.add_pcidev(pci_sw)
        e.add_nic(nic)
        e.add_nic(nic2)
        e.add_host(host)

        hosts.append(host)

    return hosts


experiments = []

e = exp.Experiment('echo-qemu-switch-enso_bm')

net = sim.SwitchNet()
net.sync = False

e.add_network(net)

servers = create_basic_hosts_with_pcie_switch(
    e,
    1,
    'server',
    net,
    sim.EnsoBMNIC,
    sim.PCISwitchSim,
    sim.QemuHost,
    EnsoLocal,
    node.EnsoEchoServer
)

clients = create_basic_hosts_with_pcie_switch(
    e,
    1,
    'client',
    net,
    sim.EnsoBMNIC,
    sim.PCISwitchSim,
    sim.QemuHost,
    EnsoLocal,
    ConfiguredEnsoGen,
    ip_start=2
)

for c in clients:
    c.wait = True

experiments.append(e)
