import srvdb

db = srvdb.SrvDb("./ping-aggregator.db")

with open("./saved_ips.txt") as f:
    content = f.read().splitlines()

ips = []
for ip in content:
    if ip not in ips:
        print("Adding node {}".format(ip))
        db.add_node(ip, False, 0, "")
        ips.append(ip)

ips = db.get_node_ips()
for ip in ips:
    print("Found IP: {}".format(ip))
