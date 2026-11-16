# Sample commands

```bash
# 1. Classic textbook example
python vlsm.py 192.168.10.0/24 Sales=100 HR=50 IT=20 Servers=10 WAN=2

# 2. Larger network, plain host counts
python vlsm.py 10.0.0.0/22 500 120 60 30 2 2

# 3. Export to CSV / JSON
python vlsm.py 172.16.0.0/16 Engineering=1000 Marketing=300 Lab=7 --format csv -o plan.csv
python vlsm.py 172.16.0.0/16 Engineering=1000 Marketing=300 Lab=7 --format json

# 4. Error case: requirements do not fit
python vlsm.py 192.168.1.0/24 200 100
```
