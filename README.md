# VLSM Calculator (Python)

A small command-line tool that takes a base network and a list of host
requirements and prints a **Variable Length Subnet Mask (VLSM)** plan.

Optional GitHub mini-project for **21CSC302J – Computer Networks**
(SRM Institute of Science and Technology), Project 4.

## What it does

Given `192.168.10.0/24` and the requirements `Sales=100 HR=50 IT=20 Servers=10 WAN=2`, it:

1. Sorts requirements from largest to smallest.
2. Picks the smallest block that fits each one (`usable hosts = 2^(32-prefix) - 2`).
3. Allocates blocks one after another, aligned on block boundaries, so nothing overlaps.
4. Prints network/CIDR, mask, first/last usable host, broadcast, usable and wasted addresses.
5. Stops with a clear error if the requirements do not fit in the base network.

Only Python's built-in `ipaddress` module is used. No `pip install` needed.

## Usage

```bash
python vlsm.py <network> <hosts> [<hosts> ...] [--format table|json|csv] [-o FILE]
```

```bash
python vlsm.py 192.168.10.0/24 Sales=100 HR=50 IT=20 Servers=10 WAN=2
python vlsm.py 10.0.0.0/22 500 120 60 30 2 2          # unnamed -> LAN1, LAN2, ...
python vlsm.py 172.16.0.0/16 Eng=1000 Lab=7 --format csv -o plan.csv
```

Requires Python 3.8+. More commands are in `examples/sample_inputs.md`.

## Example output

```
VLSM plan for 192.168.10.0/24
+---------+------+-------------------+-----------------+----------------+----------------+----------------+--------+--------+
| Subnet  | Need | Network/CIDR      | Mask            | First Host     | Last Host      | Broadcast      | Usable | Wasted |
+---------+------+-------------------+-----------------+----------------+----------------+----------------+--------+--------+
| Sales   | 100  | 192.168.10.0/25   | 255.255.255.128 | 192.168.10.1   | 192.168.10.126 | 192.168.10.127 | 126    | 26     |
| HR      | 50   | 192.168.10.128/26 | 255.255.255.192 | 192.168.10.129 | 192.168.10.190 | 192.168.10.191 | 62     | 12     |
| IT      | 20   | 192.168.10.192/27 | 255.255.255.224 | 192.168.10.193 | 192.168.10.222 | 192.168.10.223 | 30     | 10     |
| Servers | 10   | 192.168.10.224/28 | 255.255.255.240 | 192.168.10.225 | 192.168.10.238 | 192.168.10.239 | 14     | 4      |
| WAN     | 2    | 192.168.10.240/30 | 255.255.255.252 | 192.168.10.241 | 192.168.10.242 | 192.168.10.243 | 2      | 0      |
+---------+------+-------------------+-----------------+----------------+----------------+----------------+--------+--------+
Addresses allocated: 244/256 (95.3% of 192.168.10.0/24); 12 addresses still free.
```

## Screenshots

Add your own screenshots to `docs/screenshots/` and link them here:

![Example run](docs/screenshots/run1.png)
![Error case](docs/screenshots/error.png)
![Tests passing](docs/screenshots/tests.png)

## Tests

```bash
python -m unittest discover -s tests -v
```

10 tests check prefix calculation, the textbook example, no overlapping subnets,
enough usable hosts per subnet, and error handling for bad input.

## Project structure

```
vlsm.py                  main tool (logic + CLI)
tests/test_vlsm.py       unit tests
examples/                sample commands
docs/sample_output.txt   captured output
```

## What I learned

*(Rewrite this in your own words before submitting. Suggested points:)*

- Why VLSM saves addresses compared to fixed-length subnetting.
- Why the largest subnet must be allocated first (alignment on block boundaries).
- Why each subnet loses 2 addresses (network + broadcast) and why /30 is the smallest block for point-to-point links here.
- How Python's `ipaddress` module handles networks, masks and address arithmetic.
- Something that went wrong and how I fixed it.

## Possible improvements

- IPv6 support
- Reserve extra addresses for growth (e.g. +20%)
- Support /31 point-to-point links (RFC 3021)
