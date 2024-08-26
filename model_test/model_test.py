import pandas as pd
import ollama ,json

reports_df = df = pd.read_json('./reports.json', orient='records', encoding='utf-8')

wrong_reports = reports_df['wrong_report'].tolist()

models = ['llama3.1:8b', 'gemma2:9b', 'mistral-nemo:12b']

prompts = [
    'Please correct the following medical report without altering any medical facts or terminology.',
    
    'Please correct the following medical report without altering any medical facts or terminology, and if possible offer explanations for the changes you make.',
    
    'Please correct the following medical report without altering any medical facts or terminology, please provide three possible improved versions of the medical reports along with their confidence scores. Do not provide explanations.'
    ]

system_msg = """
    Role: You are an expert language model specialized in editing and refining medical reports at the Uniklinikum Aachen. Your primary task is to correct any grammatical, structural, or spelling errors in the text while preserving the accuracy of the medical information and terminology. Do not alter the medical facts, diagnoses, or treatment plans described in the report. Maintain the clinical tone and format appropriate for medical documentation.

    Most if not All of the reports you will have to correct will be in German.

    Guidelines:

    Grammar:
    Correct any grammatical errors, including verb tense, subject-verb agreement, and sentence fragments.

    Punctuation:
    Ensure proper punctuation, including the use of commas, periods, and colons. Adjust capitalization where necessary.

    Spelling:
    Correct any spelling errors, with attention to medical terminology. Ensure that all medical terms, drug names, and anatomical references are spelled correctly.

    Structure:
    Improve sentence structure for clarity and readability. Ensure that the report follows a logical flow, with each section clearly transitioning to the next. Reorganize sentences or paragraphs if necessary to enhance coherence, but do not omit or alter any medical information.

    Clarity & Conciseness:
    Simplify overly complex sentences where appropriate, ensuring that the report is clear and easy to understand for medical professionals. Remove redundant words or phrases to make the report more concise without losing essential information.
    Medical Terminology:

    Ensure that medical terminology is used accurately and consistently throughout the report.
    Do not replace or alter medical terms unless correcting an obvious spelling or grammatical error.
    Professional Tone:

    Maintain the formal and clinical tone appropriate for medical reports.
    Avoid introducing any informal language or colloquialisms.
    Output Expectations:

    Return the edited medical report with all corrections applied, clearly indicating any changes made.
    Ensure the final document is polished, professional, and ready for review by healthcare professionals.
    Important Note:

    Do not alter any factual content, diagnostic conclusions, or treatment recommendations within the report. If you encounter unclear or ambiguous language, improve its clarity without changing the intended meaning.
"""

context = None

responses = dict()

error_log = []

def test_models():
    for model in models:
        responses[model] = dict()
        for i, prompt in enumerate(prompts):
            responses[model][prompt] = []
            for wrong_report in wrong_reports:
                try:
                    response = ollama.generate(
                        model=model,
                        system=system_msg,
                        prompt=prompt + '\n' + wrong_report,
                        context=context
                    )
                    responses[model][prompt].append((wrong_report ,response))
                except Exception as e:
                    error_log.append(f'Model: {model}, Prompt: {prompt}, Report: {wrong_report}, Error: {e}')
                    responses[model][prompt].append((wrong_report ,None))
                    continue
                
            with open(f'{model}_Prompt_{i}_responses.json', 'w', encoding='utf-8') as json_file:
                json.dump(responses[model][prompt], json_file, ensure_ascii=False, indent=4)

    with open('responses.json', 'w', encoding='utf-8') as json_file:
        json.dump(responses, json_file, ensure_ascii=False, indent=4)
        

    with open('error_log.json', 'w', encoding='utf-8') as json_file:
        json.dump(error_log, json_file, ensure_ascii=False, indent=4)

    responses_df = pd.DataFrame(responses)

    responses_df.to_json('responses_df.json', orient='records', force_ascii=False)


if __name__ == '__main__':
    test_models()
