import ipaddress
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from vlsm import plan_vlsm, prefix_for_hosts, parse_requirements


class TestPrefix(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(prefix_for_hosts(100), 25)   # 126 usable
        self.assertEqual(prefix_for_hosts(126), 25)
        self.assertEqual(prefix_for_hosts(127), 24)   # needs 254
        self.assertEqual(prefix_for_hosts(50), 26)    # 62 usable
        self.assertEqual(prefix_for_hosts(20), 27)    # 30 usable
        self.assertEqual(prefix_for_hosts(10), 28)    # 14 usable
        self.assertEqual(prefix_for_hosts(2), 30)
        self.assertEqual(prefix_for_hosts(1), 30)     # minimum block

    def test_invalid(self):
        with self.assertRaises(ValueError):
            prefix_for_hosts(0)


class TestPlan(unittest.TestCase):
    def test_classic_example(self):
        plan, free = plan_vlsm("192.168.10.0/24",
                               [("A", 100), ("B", 50), ("C", 20), ("D", 10), ("E", 2)])
        got = [(s.name, f"{s.network}/{s.prefix}") for s in plan]
        self.assertEqual(got, [("A", "192.168.10.0/25"), ("B", "192.168.10.128/26"),
                               ("C", "192.168.10.192/27"), ("D", "192.168.10.224/28"),
                               ("E", "192.168.10.240/30")])
        self.assertEqual(free, 12)

    def test_no_overlap_and_inside_base(self):
        base = ipaddress.ip_network("10.0.0.0/22")
        plan, _ = plan_vlsm(str(base), [("a", 500), ("b", 120), ("c", 60), ("d", 2), ("e", 2)])
        nets = [ipaddress.ip_network(f"{s.network}/{s.prefix}") for s in plan]
        for n in nets:
            self.assertTrue(n.subnet_of(base))
        for i, a in enumerate(nets):
            for b in nets[i + 1:]:
                self.assertFalse(a.overlaps(b))

    def test_enough_usable_hosts(self):
        plan, _ = plan_vlsm("172.16.0.0/16", [("x", 1000), ("y", 300), ("z", 7)])
        for s in plan:
            self.assertGreaterEqual(s.usable_hosts, s.hosts_required)

    def test_too_many_hosts(self):
        with self.assertRaises(ValueError):
            plan_vlsm("192.168.1.0/24", [("a", 200), ("b", 100)])

    def test_bad_network(self):
        with self.assertRaises(ValueError):
            plan_vlsm("not-a-network", [("a", 10)])
        with self.assertRaises(ValueError):
            plan_vlsm("192.168.1.5/24", [("a", 10)])   # host bits set

    def test_exact_fill(self):
        plan, free = plan_vlsm("192.168.1.0/24", [("a", 126), ("b", 126)])
        self.assertEqual(free, 0)


class TestParse(unittest.TestCase):
    def test_named_and_plain(self):
        self.assertEqual(parse_requirements(["Sales=100", "50"]),
                         [("Sales", 100), ("LAN2", 50)])

    def test_bad_value(self):
        with self.assertRaises(ValueError):
            parse_requirements(["abc"])


if __name__ == "__main__":
    unittest.main()
