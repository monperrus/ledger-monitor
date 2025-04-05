#!/usr/bin/python
"""
Ledger Monitor Script
This script fetches and stores Ledger Live application version information and corresponding
cryptographic verification files (SHA512 checksums and signatures) from Ledger's servers.
The script performs the following operations:
1. Fetches the current version information from Ledger's API
2. Saves this version data to a date-stamped JSON file
3. For each version found, downloads and stores:
    - SHA512 checksum files if not already present
    - Signature files if not already present
All data is stored in the 'data' directory with appropriate naming conventions.
Dependencies:
- requests: For making HTTP requests
- json: For processing JSON data
- datetime: For timestamping files
- os: For file path operations


"""
import requests
import json
import datetime
import os

os.chdir('/home/martin/workspace/ledger-monitor')
# human readable
def fetch_ledger_versions():
    url = "https://resources.live.ledger.app/public_resources/signatures/versions.json"
    response = requests.get(url)
    data = response.json()
    # save to file
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(f"data/versions-{today}.json", "w") as f:
        json.dump(data, f, indent=2)
    return data

for x in fetch_ledger_versions():
    if x == "hello" or x == "index.html" or x == "versions.json"  or  x.endswith(".sig"):
        continue

    print(x)

    # Check if sha512sum file exists
    sha_path = f"data/{x}.txt"
    if not os.path.exists(sha_path):
        sha_url=f"https://resources.live.ledger.app/public_resources/signatures/{x}"
        shasums = requests.get(sha_url).text
        with open(sha_path, "w") as f:
            f.write(shasums)
    
    # Check if signature file exists
    sig_path = f"data/{x}.sig"
    if not os.path.exists(sig_path):
        sig_url=f"https://resources.live.ledger.app/public_resources/signatures/{x}.sig"
        print(sig_url)
        req = requests.get(sig_url)
        sig = req.content
        # print(x, sig)
        assert req.status_code == 200
        with open(sig_path, "wb") as f:
            f.write(sig)

    cmd = f"openssl dgst -sha256 -verify ledgerlive.pem -signature {sig_path} {sha_path}"
    # print(cmd)
    os.system(cmd)

os.system("git add data")
os.system("git all")
