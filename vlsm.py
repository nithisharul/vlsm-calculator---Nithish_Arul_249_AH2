#!/usr/bin/env python3
"""
VLSM Calculator
===============
Takes a base network and a list of host requirements, then prints a
Variable Length Subnet Mask (VLSM) allocation plan.

Course : 21CSC302J - Computer Networks (SRM IST)
Uses   : only Python's built-in `ipaddress` module (no external packages).
"""

import argparse
import csv
import io
import ipaddress
import json
import sys
from dataclasses import dataclass, asdict

MIN_HOSTS_PER_SUBNET = 2   # smallest block we hand out is a /30 (2 usable hosts)


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------
@dataclass
class Subnet:
    name: str
    hosts_required: int
    network: str
    prefix: int
    mask: str
    first_host: str
    last_host: str
    broadcast: str
    usable_hosts: int
    wasted: int


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------
def prefix_for_hosts(hosts: int, max_prefix: int = 30) -> int:
    """Return the longest prefix length (smallest block) that fits `hosts`.

    Usable hosts in a block = 2^(32 - prefix) - 2  (network + broadcast excluded).
    """
    if hosts < 1:
        raise ValueError(f"Host count must be at least 1 (got {hosts}).")
    hosts = max(hosts, MIN_HOSTS_PER_SUBNET)
    host_bits = 2
    while (2 ** host_bits) - 2 < hosts:
        host_bits += 1
    prefix = 32 - host_bits
    if prefix > max_prefix:
        prefix = max_prefix
    return prefix


def plan_vlsm(base_network: str, requirements):
    """Build a VLSM plan.

    base_network : e.g. "192.168.10.0/24"
    requirements : list of (name, hosts) tuples
    Returns      : (list[Subnet], free_addresses_left)
    Raises       : ValueError if the requirements do not fit in the base network.
    """
    try:
        base = ipaddress.ip_network(base_network, strict=True)
    except ValueError as exc:
        raise ValueError(f"Invalid network '{base_network}': {exc}") from None
    if base.version != 4:
        raise ValueError("Only IPv4 networks are supported.")
    if not requirements:
        raise ValueError("Provide at least one host requirement.")

    # Largest requirement first -> blocks stay naturally aligned, no wasted gaps.
    ordered = sorted(requirements, key=lambda r: r[1], reverse=True)

    # Quick feasibility check before allocating anything.
    total_needed = sum(2 ** (32 - prefix_for_hosts(h)) for _, h in ordered)
    if total_needed > base.num_addresses:
        raise ValueError(
            f"Requirements need {total_needed} addresses (after rounding to "
            f"power-of-two blocks) but {base} only has {base.num_addresses}."
        )

    plan = []
    cursor = int(base.network_address)
    end = int(base.broadcast_address)

    for name, hosts in ordered:
        prefix = prefix_for_hosts(hosts)
        size = 2 ** (32 - prefix)
        if cursor % size:                       # align to block boundary
            cursor += size - (cursor % size)
        if cursor + size - 1 > end:
            raise ValueError(f"Ran out of address space while allocating '{name}'.")

        net = ipaddress.ip_network((cursor, prefix))
        usable = size - 2
        plan.append(Subnet(
            name=name,
            hosts_required=hosts,
            network=str(net.network_address),
            prefix=prefix,
            mask=str(net.netmask),
            first_host=str(net.network_address + 1),
            last_host=str(net.broadcast_address - 1),
            broadcast=str(net.broadcast_address),
            usable_hosts=usable,
            wasted=usable - hosts,
        ))
        cursor += size

    free_left = end - cursor + 1
    return plan, free_left


# --------------------------------------------------------------------------
# Output formatters
# --------------------------------------------------------------------------
def format_table(plan, base_network, free_left):
    headers = ["Subnet", "Need", "Network/CIDR", "Mask", "First Host",
               "Last Host", "Broadcast", "Usable", "Wasted"]
    rows = [[s.name, s.hosts_required, f"{s.network}/{s.prefix}", s.mask,
             s.first_host, s.last_host, s.broadcast, s.usable_hosts, s.wasted]
            for s in plan]
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]

    def line(cells):
        return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    out = [f"VLSM plan for {base_network}", sep, line(headers), sep]
    out += [line(r) for r in rows]
    out.append(sep)

    used = sum(2 ** (32 - s.prefix) for s in plan)
    total = used + free_left
    out.append(f"Addresses allocated: {used}/{total} "
               f"({used / total * 100:.1f}% of {base_network}); "
               f"{free_left} addresses still free.")
    return "\n".join(out)


def format_json(plan, base_network, free_left):
    return json.dumps({"base_network": base_network,
                       "free_addresses": free_left,
                       "subnets": [asdict(s) for s in plan]}, indent=2)


def format_csv(plan):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(asdict(plan[0]).keys()))
    writer.writeheader()
    for s in plan:
        writer.writerow(asdict(s))
    return buf.getvalue()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def parse_requirements(items):
    """Accept '100' or 'Sales=100'. Unnamed entries become LAN1, LAN2, ..."""
    reqs = []
    for i, item in enumerate(items, start=1):
        if "=" in item:
            name, _, count = item.partition("=")
            name = name.strip() or f"LAN{i}"
        else:
            name, count = f"LAN{i}", item
        try:
            reqs.append((name, int(count)))
        except ValueError:
            raise ValueError(f"'{item}' is not a valid host count "
                             f"(use e.g. 100 or Sales=100).") from None
    return reqs


def build_parser():
    p = argparse.ArgumentParser(
        prog="vlsm",
        description="Generate a VLSM subnetting plan from a base network and host counts.",
        epilog="Example: python vlsm.py 192.168.10.0/24 Sales=100 HR=50 IT=20 WAN=2",
    )
    p.add_argument("network", help="Base network in CIDR form, e.g. 192.168.10.0/24")
    p.add_argument("hosts", nargs="+",
                   help="Host counts, either plain (100) or named (Sales=100)")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table",
                   help="Output format (default: table)")
    p.add_argument("-o", "--output", help="Write the result to a file instead of the screen")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        reqs = parse_requirements(args.hosts)
        plan, free_left = plan_vlsm(args.network, reqs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        text = format_json(plan, args.network, free_left)
    elif args.format == "csv":
        text = format_csv(plan)
    else:
        text = format_table(plan, args.network, free_left)

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as fh:
            fh.write(text + ("\n" if not text.endswith("\n") else ""))
        print(f"Saved to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
