# Ping21AggregatorE16

## Overview
This is a Ping21 Aggregator that will select for lowest price among the Ping21 nodes when a request comes in.  It will charge the client the
cost charged by all the Ping21 nodes plus 1,000 satoshis for the aggregation service.

### Example Usage
You want to ping bitcoin.org and get stats about the latency.  You can run this command to get ping stats with 2 nodes:
```
$ 21 buy http://10.244.113.158:7018/ --data '{"nodes": 2, "website": "bitcoin.org"}'
```
You will get the following stats from the 2 nodes:
```
[
    {
        "ping": [
            "PING bitcoin.org (208.64.123.130) 64(92) bytes of data.",
            "72 bytes from 208.64.123.130: icmp_seq=1 ttl=53 time=239 ms",
            "72 bytes from 208.64.123.130: icmp_seq=2 ttl=53 time=247 ms",
            "72 bytes from 208.64.123.130: icmp_seq=3 ttl=53 time=239 ms",
            "--- bitcoin.org ping statistics ---",
            "3 packets transmitted, 3 received, 0% packet loss, time 1999ms",
            "rtt min/avg/max/mdev = 239.625/242.389/247.814/3.857 ms"
        ],
        "price_paid": 5,
        "server": {
            "loc": "38.6214,21.4078",
            "region": "West Greece",
            "org": "AS1241 Forthnet",
            "country": "GR",
            "city": "Agrinio"
        }
    },
    {
        "ping": [
            "PING bitcoin.org (208.64.123.130) 64(92) bytes of data.",
            "72 bytes from 208.64.123.130: icmp_seq=1 ttl=55 time=23.2 ms",
            "72 bytes from 208.64.123.130: icmp_seq=2 ttl=55 time=25.0 ms",
            "72 bytes from 208.64.123.130: icmp_seq=3 ttl=55 time=23.5 ms",
            "--- bitcoin.org ping statistics ---",
            "3 packets transmitted, 3 received, 0% packet loss, time 2002ms",
            "rtt min/avg/max/mdev = 23.276/23.962/25.034/0.767 ms"
        ],
        "price_paid": 5,
        "server": {
            "org": "AS7922 Comcast Cable Communications, LLC",
            "region": "California",
            "postal": "95624",
            "city": "Elk Grove",
            "country": "US",
            "loc": "38.4412,-121.3064"
        }
    }
]

You spent: 1010 satoshis. Remaining 21.co balance: XXX satoshis.
```
You can see that each node charged 5 satoshis for the call.  The total cost was 1,000 + 5 + 5 = 1,010.
