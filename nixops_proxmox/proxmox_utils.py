# -*- coding: utf-8 -*-

import proxmoxer.backends.https
from proxmoxer import ProxmoxAPI
from typing import Optional, List
import socket

def connect(
        server_url: str,
        username: str,
        *,
        password: Optional[str] = None,
        token_name: Optional[str] = None,
        token_value: Optional[str] = None,
        verify_ssl: bool = False,
        use_ssh: bool = False):

    kwargs = {
        "host": server_url,
        "user": username,
        "password": password,
        "backend": "ssh_paramiko" if use_ssh else "https"
    }

    if token_name and token_value and not use_ssh:
        kwargs["token_name"] = token_name
        kwargs["token_value"] = token_value

    if not use_ssh:
        kwargs['verify_ssl'] = verify_ssl


    api = ProxmoxAPI(**kwargs)

    # check if API is working.
    try:
        nodes = api.nodes().get()
        if not nodes:
            raise Exception(f"Failed to connect to Proxmox server '{server_url}@{username}' OR empty Proxmox cluster (no nodes found), verify credentials")
    except proxmoxer.backends.https.AuthenticationError:
            raise Exception(f"Failed to connect to Proxmox server '{server_url}@{username}', verify credentials (authentication error)")

    return api

def tcp_ping(host, port: int = 22, max_count: int = 20, timeout: int = 3):
    failed = 0
    count = 0
    rtt = []
    successes = []
    while count < max_count:
        success = False
        count += 1

        s = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)

        s.settimeout(timeout)

        start = time.time()
        try:
            s.connect(host, port)
            s.shutdown(socket.SHUT_RD)
            success = True
        except socket.timeout:
            failed += 1
        except OSError as e:
            failed += 1

        elapsed = time.time() - start
        successes.append(success)
        rtt.append(elapsed)

        if count < max_count:
            time.sleep(1)

    return rtt, successes

def select_fastest_ip_address(ips: List[str]):
    """
    Select the fastest & reachable IP address based on TCP ping.
    """
    delays = {}
    successes = {}
    for ip in ips:
        rtts, succ = tcp_ping(ip)
        nbSuccess = succ.count(True)
        delays[ip] = rtts
        successes[ip] = nbSuccess

    return sorted(ips, key=lambda ip: (successes[ip], avg(delays[ip])))
