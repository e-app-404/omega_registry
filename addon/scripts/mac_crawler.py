import os
import re
import csv
from collections import defaultdict

MAC_REGEX = re.compile(
    r'([0-9a-fA-F]{2}([-:])(?:[0-9a-fA-F]{2}\2){4}[0-9a-fA-F]{2})'
)

def extract_context(lines, idx, window=10):
    start = max(0, idx - window)
    end = min(len(lines), idx + window + 1)
    return lines[start:end]

# OUI vendor lookup (first 3 octets)
OUI_VENDOR = {
    '44:4f:8e': 'Wiz',
    'cc:40:85': 'Wiz',
    '6c:29:90': 'Wiz',
    'd8:a0:11': 'Wiz',
    '9c:53:22': 'Tapo',
    '98:25:4a': 'TP-Link',
    'e8:16:56': 'Broadlink',
    'c4:5b:be': 'Ambient Weather',
    'c0:f5:35': 'SDMC',
    '32:db:c3': 'Apple',
    '24:90:9a': 'Big Field Global PTE. Ltd.',
    'c4:82:e1': 'Enshine',
    '1c:61:b4': 'Tapo',
    '30:de:4b': 'Tapo',
    'a8:47:4a': 'Unknown',
    'fc:67:1f': 'Unknown',
    '2c:cf:67': 'Raspberry Pi (Trading) Ltd',
    '80:4a:f2': 'Sonos',
    'b1:81:11': 'Apple Inc.',
    'ff:fe:6e': 'Wiz',
    'c4:38:75': 'Sonos',
    'cc:8d:a2': 'Unknown',
    'd4:ad:fc': 'Govee',
    'cc:40:85': 'Wiz',
    'c8:69:cd': 'Unknown',
    'a6:09:17': 'Unknown',
    '38:8b:59': 'Unknown',
    '16:8c:50': 'Unknown',
    'f0:a7:31': 'Unknown',
    '90:09:d0': 'Unknown',
    '10:52:1c': 'Unknown',
    '7c:49:eb': 'Unknown',
    '88:20:0d': 'Unknown',
    '34:7e:5c': 'Unknown',
    'fc:3c:d7': 'Unknown',
    'c2:0c:92': 'Unknown',
    'c8:12:0b': 'Unknown',
    'a8:6e:84': 'Unknown',
    '70:66:2a': 'Unknown',
    '1c:90:ff': 'Unknown',
    '66:2f:d0': 'Unknown',
    'b1:81:11': 'Apple Inc.'
}

def guess_vendor(mac):
    prefix = mac[:8]
    return OUI_VENDOR.get(prefix, '')

def find_mac_blocks(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            for match in MAC_REGEX.findall(line):
                mac = match[0].replace('-', ':').lower()
                context = extract_context(lines, idx)
                context_str = ''.join(context)
                name = ""
                manufacturer = ""
                # Try to find device name
                name_match = re.search(r'"(?:name|friendly_name|omega_name|internal_name|entity_id|canonical_id|model|type|description)"\s*:\s*"([^"]+)"', context_str, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1)
                # Try to find manufacturer
                manufacturer_match = re.search(r'"manufacturer"\s*:\s*"([^"]+)"', context_str, re.IGNORECASE)
                if manufacturer_match:
                    manufacturer = manufacturer_match.group(1)
                # Fallback: OUI lookup if manufacturer missing
                if not manufacturer:
                    manufacturer = guess_vendor(mac)
                # Fallback: use filename as name if nothing else
                if not name:
                    name = os.path.splitext(os.path.basename(filepath))[0]
                results.append((mac, name, manufacturer, os.path.basename(filepath)))
    except Exception:
        pass
    return results

def crawl_for_mac_blocks(root='.'):
    mac_blocks = defaultdict(lambda: ('', '', ''))
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(('.json', '.yaml', '.yml', '.txt', '.log', '.conf')):
                filepath = os.path.join(dirpath, filename)
                for mac, name, manufacturer, source in find_mac_blocks(filepath):
                    # Prefer richer metadata if found again
                    prev_name, prev_man, _ = mac_blocks[mac]
                    if name and (not prev_name or len(name) > len(prev_name)):
                        mac_blocks[mac] = (name, manufacturer, source)
                    elif not prev_name:
                        mac_blocks[mac] = (name, manufacturer, source)
    return mac_blocks

def main():
    mac_blocks = crawl_for_mac_blocks('.')
    yaml_lines = [
        "network_scanner:",
        '  ip_range: "10.100.1.0/24 10.1.1.0/24"'
    ]
    for idx, (mac, (name, manufacturer, source)) in enumerate(mac_blocks.items(), 1):
        label = f"{name or source}"
        yaml_lines.append(
            f'  mac_mapping_{idx}: "{mac};{label};{manufacturer}"'
        )
    with open('mac_scan_output.log', 'w') as f:
        f.write('\n'.join(yaml_lines))
    print("MAC scan complete. Output written to mac_scan_output.log")

if __name__ == "__main__":
    main()
