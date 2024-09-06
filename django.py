#example data in csv 
server_name
iaas001.svr.com
iaas002.svr.com
iaas001.svr.com
iaas23.svr.com
userfriendly.com
iaas001.svr.com
# api response after chunk data
{
    "iaas001.svr.com": ["ip1", "ip2"],
    "iaas002.svr.com": ["ip3"],
    "iaas23.svr.com": [],
    "userfriendly.com": ["ip4", "ip5", "ip6"]
}
#expected output
server_name         api_result
0  iaas001.svr.com              ip1
1  iaas001.svr.com              ip2
2  iaas002.svr.com              ip3
3  iaas23.svr.com
4  userfriendly.com              ip4
5  userfriendly.com              ip5
6  userfriendly.com              ip6
---------------------------------------------------
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

def call_api(server_name):
    # Replace with your actual API call logic
    api_url = f"https://your_api_endpoint/{server_name}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error calling API for {server_name}: {response.status_code}")
        return []

def process_data(df_chunk, seen_servers):
    # Extract unique server names
    unique_server_names = df_chunk['server_name'].unique().tolist()

    # Filter out servers already seen
    server_names = [server_name for server_name in unique_server_names if server_name not in seen_servers]

    # Make API calls concurrently
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_api, server_name) for server_name in server_names]
        results = {server_name: future.result() for server_name, future in zip(server_names, futures)}

    # Update seen servers
    seen_servers.update(server_names)

    # Convert results to DataFrame
    result_df = pd.DataFrame.from_dict(results, orient='index').reset_index()
    result_df.columns = ['server_name', 'api_result']

    # Handle empty lists
    result_df['api_result'] = result_df['api_result'].apply(lambda x: x if isinstance(x, list) else [])

    return result_df

# Read CSV in chunks
df = pd.read_csv('your_data.csv', chunksize=10000)

# Initialize seen servers set
seen_servers = set()

# Process each chunk and concatenate results
final_df = pd.concat([process_data(chunk, seen_servers) for chunk in df])

# Expand rows based on the 'api_result' column
final_df = final_df.explode('api_result')

print(final_df)
---------------------------------------------------------
