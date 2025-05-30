import sys
from datetime import datetime

def extract_timestamp(line):
    try:
        time_str = line.split(']')[0].strip('[')
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        raise ValueError(f"Invalid log format in line: {line}\nError: {e}")

def compute_log_duration(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if len(lines) < 2:
        raise ValueError("Log file must contain at least two lines")

    start_time = extract_timestamp(lines[0])
    end_time = extract_timestamp(lines[-1])

    duration = end_time - start_time
    return duration

if __name__ == '__main__':

    print(compute_log_duration(sys.argv[1]))
