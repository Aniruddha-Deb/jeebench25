import json
import re
import sys

RESULT_FILE = sys.argv[1]

def main():

    cost_per_input_token = {
        'o4-mini': 1.1 / 1e6,
        'gpt-4o': 2.5 / 1e6,
        'o3': 10 / 1e6,
    }

    cost_per_output_token = {k: v*4 for k,v in cost_per_input_token.items()}

    model_name = None
    for cdt_model_name in cost_per_input_token:
        if cdt_model_name in RESULT_FILE:
            model_name = cdt_model_name

    if model_name is None:
        raise RuntimeError("File name should have model name in it")

    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_input_token_cost = 0
    total_output_token_cost = 0

    with open(RESULT_FILE, 'r') as result_file:
        results_json = json.load(result_file)
        for question in results_json:
            usage = question['usage']
            num_input_tokens = usage['input_tokens']
            num_output_tokens = usage['output_tokens']
            total_input_tokens += num_input_tokens
            total_output_tokens += num_output_tokens

    total_input_token_cost = total_input_tokens * cost_per_input_token[model_name]
    total_output_token_cost = total_output_tokens * cost_per_output_token[model_name]

    total_cost = total_input_token_cost + total_output_token_cost

    total_tokens = total_input_tokens + total_output_tokens
    print(f"Total tokens: {total_tokens}")
    print(f"   input: {total_input_tokens} ({total_input_tokens * 100 / total_tokens:.2f}%)")
    print(f"  output: {total_output_tokens} ({total_output_tokens * 100 / total_tokens:.2f}%)")

    print(f"Total cost: ${total_cost:.6f}")
    print(f"   input: ${total_input_token_cost:.6f} ({total_input_token_cost * 100 / total_cost:.2f}%)")
    print(f"  output: ${total_output_token_cost:.6f} ({total_output_token_cost * 100 / total_cost:.2f}%)")

if __name__ == "__main__":
    main()
