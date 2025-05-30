import json
import sys

RESULT_DIR = "results"

RESULT_FILE = sys.argv[1]


def score_sca(gold, pred):
    if gold == 'BONUS' or pred == gold:
        return 3
    if pred is None or pred == 'O':
        return 0
    return -1

def score_m(gold, pred):
    if gold == 'BONUS' or pred == gold:
        return 4
    if pred is None or pred == 'O':
        return 0
    return -1

def score_mca(gold, pred):
    if gold == 'BONUS':
        return 4
    if pred is None or pred == 'O':
        return 0
    pred_set = set(pred.split(','))
    gold_set = set(gold)

    if pred_set.intersection(gold_set) == gold_set:
        return 4
    if pred_set.intersection(gold_set) == pred_set:
        return len(pred_set)

    return -1

def score_nt(gold, pred):
    if gold == 'BONUS':
        return 4

    if '|' in gold:
        gold_cdts = gold.split('|')
    else:
        gold_cdts = [gold]

    for gold_cdt in gold_cdts:
        if gold_cdt[0] == '[':
            gold_range = [float(n) for n in gold_cdt[1:-1].split(',')]
            if gold_range[0] <= float(pred) <= gold_range[1]:
                return 4
        elif float(pred) == float(gold_cdt):
            return 4
    return 0

def main():

    score_funcs = {
        'SCA': score_sca,
        'MCA': score_mca,
        'NT': score_nt,
        'M': score_m
    }

    max_scores = {
        'SCA': 3,
        'MCA': 4,
        'NT': 4,
        'M': 4
    }

    score = 0
    max_score = 0
    score_by_subject = {'math': 0, 'physics': 0, 'chemistry': 0}
    correct_output_token_counts = 0
    incorrect_output_token_counts = 0
    num_correct = 0
    num_incorrect = 0
    with open(RESULT_FILE, 'r') as result_file:
        results_json = json.load(result_file)
        for question in results_json:
            q_score = score_funcs[question['type']](question['ans'], question['pred'])
            if q_score < 3:
                print(f"---------")
                print(f"{question['subject']} Q{question['num']} incorrect: expected {question['ans']}, got {question['pred']}")
                print(question['response'])
                print(f"---------")
                num_incorrect += 1
                if 'usage' in question:
                    incorrect_output_token_counts += question['usage']['output_tokens']
            else:
                num_correct += 1
                if 'usage' in question:
                    correct_output_token_counts += question['usage']['output_tokens']
            score += q_score
            max_score += max_scores[question['type']]
            score_by_subject[question['subject']] += q_score

    print(f"{score}/{max_score}")
    for subject, score in score_by_subject.items():
        print(subject, f"{score}/{max_score//3}")

    print("")
    print(f"output tokens/q for correct answers: {correct_output_token_counts/num_correct}")
    print(f"output tokens/q for incorrect answers: {incorrect_output_token_counts/num_incorrect}")

if __name__ == "__main__":
    main()
