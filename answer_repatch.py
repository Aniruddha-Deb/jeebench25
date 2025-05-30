import pandas as pd
import os
import glob
import json

PAPER_ID = 2

csv_df = pd.read_csv(f"dataset/jeea25_p{PAPER_ID}.csv")  # Replace with your actual file path

# Create a lookup dict with (num, subject) as key
answer_map = {
    (str(row['num']), row['subject']): row['ans']
    for _, row in csv_df.iterrows()
}

json_files = glob.glob(os.path.join("results/final_copy", f"*p{PAPER_ID}*.json"))

for json_file in json_files:
    # Load dataset 2 (JSON)
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Replace the 'ans' field using the lookup
    for record in json_data:
        key = (str(record['num']), record['subject'])
        if key in answer_map:
            record['ans'] = answer_map[key]

    # Write the updated JSON back
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

