import json
import csv
from pathlib import Path

jsonl_file = Path(__file__).parent / 'measurements.jsonl'
csv_file = Path(__file__).parent / 'measurements.csv'

def convert():
    if not jsonl_file.exists():
        print("JSONL file not found.")
        return
        
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    data = [json.loads(line) for line in lines if line.strip()]

    if not data:
        print("No data to convert.")
        return
        
    # Get all possible keys just in case some rows have different keys
    keys = set()
    for row in data:
        keys.update(row.keys())
        
    # Sort keys to have a consistent order (or use the order from the first row)
    ordered_keys = list(data[0].keys())
    for k in keys:
        if k not in ordered_keys:
            ordered_keys.append(k)

    # utf-8-sig adds BOM so Excel opens it with correct encoding automatically
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=ordered_keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
        
    print(f"Successfully created {csv_file}")

if __name__ == '__main__':
    convert()
