from openai import OpenAI
import pandas as pd
from pathlib import Path
import pickle
import re
from jinja2 import Environment, FileSystemLoader
from dotenv import dotenv_values
from time import sleep
import sys
from datetime import datetime
import logging
import json
import base64

# -------------------------------------------------
# Configuration
# -------------------------------------------------
RUN_TIME   = datetime.now().strftime("%Y%m%dT%H%M%S")
PAPER_NUM  = 2
DEBUG      = False
DATA_DIR   = "dataset"
RESULT_DIR = "results"
PROMPT_DIR = "prompts"
LOG_DIR    = "logs"
LOG_LEVEL  = logging.DEBUG if DEBUG else logging.INFO
MODEL_NAME = "o3"
SLEEP      = 5

DATA_FILE   = f"{DATA_DIR}/jeea25_p{PAPER_NUM}.csv"
IMAGE_DIR   = f"{DATA_DIR}/images"
OUTPUT_FILE = f"{RESULT_DIR}/{'DEBUG_' if DEBUG else ''}jeea25_p{PAPER_NUM}_{MODEL_NAME}_{RUN_TIME}.json"
LOG_FILE    = f"{LOG_DIR}/{'DEBUG_' if DEBUG else ''}jeea25_p{PAPER_NUM}_{MODEL_NAME}_{RUN_TIME}.log"

QUESTION_TYPES = ["SCA", "MCA", "NT", "M"]

# -------------------------------------------------
# Setup
# -------------------------------------------------

def setup_logger(logfile, level):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

logger = setup_logger(LOG_FILE, LOG_LEVEL)

client = OpenAI(api_key=dotenv_values()['OPENAI_API_KEY'])

env = Environment(loader=FileSystemLoader("prompts"))

with open(f"{PROMPT_DIR}/system.txt", "r") as f:
    system_prompt = f.read().strip()

templates = {
    tmp : env.get_template(f"{tmp.lower()}.j2") for tmp in QUESTION_TYPES
}

# -------------------------------------------------
# Logic
# -------------------------------------------------
def create_prompt(row):
    logger.debug("Creating prompt for question %s", row["text"])
    qtype = row["type"]
    template = templates[qtype]
    context = {
        "question": row["text"],
    }
    if qtype != "NT":
        context["options"] = [row["optA"], row["optB"], row["optC"], row["optD"]]

    return template.render(context)

FINAL_ANSWER_RGX = re.compile(r"\\boxed{\s*([ABCDO\d,.-]+)\s*}")

def extract_final_answer(text):
    match = FINAL_ANSWER_RGX.search(text)
    return match.group(1) if match else None

IMAGE_RGX = re.compile(r'!\[.*?\]\((.*?)\)')

def extract_image_paths(text):
    return IMAGE_RGX.findall(text)

def strip_image_links(text):
    return IMAGE_RGX.sub('', text).strip()

def b64_encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def prompt_to_multimodal_content(prompt):
    content = []

    image_paths = extract_image_paths(prompt)
    cleaned_question = strip_image_links(prompt)

    logger.info("Cleaned question: %s", cleaned_question)

    content.append({"type": "input_text", "text": cleaned_question})

    # Add all images in sequence
    for path in image_paths:
        full_path = Path(DATA_DIR) / path
        content.append({
            "type": "input_image",
            "image_url": f"data:image/png;base64,{b64_encode_image(full_path)}"
        })

    return content


def call_openai(prompt, model=MODEL_NAME):
    logger.info("Calling OpenAI model %s", model)
    input = []
    if model == 'gpt-4o' or model == 'gpt-4.1':
        # not reasoning model - add system prompt
        input.append({
            "role": "developer",
            "content": system_prompt
        })
    input.append({
        "role": "user",
        "content": prompt_to_multimodal_content(prompt)
    })
    try:
        response = client.responses.create(model=model, input=input)
        return response
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def main():
    df = pd.read_csv(DATA_FILE)

    results = []

    for idx, row in df.iterrows():
        prompt = create_prompt(row)
        response = call_openai(prompt)
        final_ans = extract_final_answer(response.output_text)

        logger.info("Got final answer %s for question %d", final_ans, idx+1)

        results.append({
            "num": row["num"],
            "subject": row["subject"],
            "type": row["type"],
            "ans": row["ans"],
            "pred": final_ans,
            "response": response.output_text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "cached_input_tokens": response.usage.input_tokens_details.cached_tokens,
                "output_tokens": response.usage.output_tokens,
                "reasoning_tokens": response.usage.output_tokens_details.reasoning_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })

        # Save results on each call - prevents loss of info on errors
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        if DEBUG:
            break
        
        sleep(SLEEP)

    logger.info(f"Saved {len(results)} result(s) to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
