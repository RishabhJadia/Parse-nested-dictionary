from collections import defaultdict

D1 = {'1414': [1, 2], '1413': [3, 4]}
D2 = {1: 'app_id', '2': 'appid', 3: 'app_id', 4: 'app_id'}

output = defaultdict(list)

for port, ips in D1.items():
    for ip in ips:
        app_key = D2[ip]
        output[app_key].append((int(port), ip))

result = {}
for app_key, ports_ips in output.items():
    ports_ips.sort()
    prev_port = None
    for port, ip in ports_ips:
        if port != prev_port:
            result.setdefault(app_key, []).append({'port': port, 'ips': []})
            prev_port = port
        result[app_key][-1]['ips'].append(ip)

print(result)

----------------------------------------------------------------------------------------

D1 = {'1414': [1, 2], '1413': [3, 4]}
D2 = {1: 'app_id', '2': 'appid', 3: 'app_id', 4: 'app_id'}

output = {}
for key, values in D1.items():
    for value in values:
        app_key = D2.get(value)
        if app_key:
            if app_key not in output:
                output[app_key] = []
            existing_port = next((d for d in output[app_key] if d['port'] == int(key)), None)
            if existing_port:
                existing_port['ips'].append(value)
            else:
                output[app_key].append({'port': int(key), 'ips': [value]})

print(output)
---------------------------------------------------------------------------
from collections import defaultdict

D1 = {'1414': [1, 2], '1413': [3, 4]}
D2 = {1: 'app_id', '2': 'appid', 3: 'app_id', 4: 'app_id'}

output = defaultdict(list)

for port, ips in D1.items():
    for ip in ips:
        app_key = D2[ip]
        output[app_key].append({'port': int(port), 'ips': [{'ip': ip, 'first': ip, 'last': ip}]})

result = {}
for app_key, ports_ips in output.items():
    ports_ips.sort(key=lambda x: x['port'])
    prev_port = None
    for port_ip in ports_ips:
        port = port_ip['port']
        ip = port_ip['ips'][0]['ip']
        if port != prev_port:
            result.setdefault(app_key, []).append({'port': port, 'ips': []})
            prev_port = port
        result[app_key][-1]['ips'].append({'ip': ip, 'first': ip, 'last': ip})

print(result)
{
    'app_id': [
        {'port': 1413, 'ips': [{'ip': 3, 'first': 3, 'last': 3}, {'ip': 4, 'first': 4, 'last': 4}]},
        {'port': 1414, 'ips': [{'ip': 1, 'first': 1, 'last': 1}, {'ip': 2, 'first': 2, 'last': 2}]}
    ],
    'appid': [
        {'port': 1414, 'ips': [{'ip': 1, 'first': 1, 'last': 1}, {'ip': 2, 'first': 2, 'last': 2}]}
    ]
}
