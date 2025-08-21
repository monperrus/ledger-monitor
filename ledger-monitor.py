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
import hashlib

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
    data.reverse()
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
        
        # Parse the SHA512 checksums into a dictionary
        sha_dict = {}
        for line in shasums.strip().split('\n'):
            line = line.strip()
            parts = line.split()
            if len(parts) == 2:
                checksum, filename = parts
                sha_dict[filename] = checksum

                download_path = f"data/{filename}.touch"
                if not os.path.exists(download_path):
                    download_url = f"https://download.live.ledger.com/{filename}"
                    response = requests.get(download_url)

                    # Compute SHA512 of downloaded content
                    sha512_hash = hashlib.sha512(response.content).hexdigest()

                    # Check against reference
                    if filename in sha_dict and sha512_hash == sha_dict[filename]:
                        print(f"✓ SHA512 verified for {filename}")
                    else:
                        raise Exception (f"✗ SHA512 mismatch for {download_url} (expected {sha_dict.get(filename, 'unknown')} from {sha_url}, got {sha512_hash})")
                    with open(download_path, "w") as f:
                        f.write("checked")

        # only at the end we write it
        with open(sha_path, "w") as f:
            f.write(shasums)

    # 
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
    return_code = os.system(cmd)
    # assert return_code == 0, f"Verification failed for {x} with return code {return_code}"

os.system("git add data")
os.system("git commit -m 'Update signatures'")
