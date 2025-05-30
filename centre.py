import pandas as pd

df = pd.read_csv("dataset/exam_centres_2024.csv")

print(f"Got {len(df)} centres")

exclude_keywords = ['iON', 'TCS', 'University', 'Engineering', 'Institute', 'College', 'School', 'Polytechnic', 'Exam', 'Academy']

mask = ~df['Centre Name'].str.contains('|'.join(exclude_keywords), case=False, na=False)

filtered_df = df[mask]
print(filtered_df)
print(f"Got {len(filtered_df)} third-party non-educational centres out of {len(df)} centres")
