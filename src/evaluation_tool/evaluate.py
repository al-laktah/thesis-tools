"""This module contains the functions to evaluate the performance of the models."""

import os
import json
from typing import Any, Dict, List, Union
from difflib import SequenceMatcher
import diff_match_patch as dmp_module
import language_tool_python as ltp
from sqlalchemy.orm import Session
from ollama import ResponseError, generate
from .db import Ris, Models, Prompts
from .util import save_to_json, get_whitelist


# duration metrics
def get_duration_metrics(responses: Dict[str, Any]) -> Dict[str, Any]:
    """function to get the duration metrics"""
    duration_metrics = {
        "load_durations": [],
        "prompt_eval_durations": [],
        "eval_counts": [],
        "eval_durations": [],
        "eval_durations_t/s": [],
    }

    for response in responses:
        duration_metrics["load_durations"].append(response["raw"]["load_duration"])
        duration_metrics["prompt_eval_durations"].append(
            response["raw"]["prompt_eval_duration"]
        )
        duration_metrics["eval_counts"].append(response["raw"]["eval_count"])
        duration_metrics["eval_durations"].append(response["raw"]["eval_duration"])
        duration_metrics["eval_durations_t/s"].append(
            int(
                response["raw"]["eval_count"]
                // (response["raw"]["eval_duration"] / 10**9)
            )
        )

    return duration_metrics


# Difference Metrics
def sm_similarity_ratio(input_report, output_report):
    """function to calculate the similarity ratio using SequenceMatcher"""
    return SequenceMatcher(None, output_report, input_report).ratio()


def levenshtein_distance(input_report, output_report):
    """function to calculate the levenshtein distance"""
    dmp = dmp_module.diff_match_patch()
    return dmp.diff_levenshtein(dmp.diff_main(input_report, output_report))


def levenshtein_distance_ratio(input_report, output_report):
    """function to calculate the levenshtein distance ratio"""
    distance = levenshtein_distance(input_report, output_report)
    ratio = distance / max(len(input_report), len(output_report))
    return distance, ratio


def get_difference_metrics(
    responses: Dict[str, Any], session: Session
) -> Dict[str, Any]:
    """function to get the diffrence metrics"""
    difference_metrics = {
        "sm_similarity_ratios": [],
        "levenshtein_distances": [],
        "levenshtein_distance_ratios": [],
        "levenshtein_distance_inverse_ratios": [],
    }

    for response in responses:
        ris = Ris.get_by_id(session, response["ris_id"])
        if ris.revision_1 is not None:
            input_report = ris.revision_1
        elif ris.revision_2 is not None:
            input_report = ris.revision_2
        else:
            continue

        output_report = response["raw"]["response"]

        difference_metrics["sm_similarity_ratios"].append(
            sm_similarity_ratio(input_report, output_report)
        )
        distance, ratio = levenshtein_distance_ratio(input_report, output_report)
        difference_metrics["levenshtein_distances"].append(distance)
        difference_metrics["levenshtein_distance_ratios"].append(ratio)
        difference_metrics["levenshtein_distance_inverse_ratios"].append(1 - ratio)

    return difference_metrics


# Language Tool Metrics
def language_tool_spelling_check(lang_tool: ltp.LanguageTool, output_report, vocab_dir):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"TYPOS"}

    misspelled = []
    whitelist = get_whitelist(vocab_dir)

    try:
        matches = lang_tool.check(output_report)
        for match in matches:
            word = match.context[
                match.offsetInContext : match.offsetInContext + match.errorLength
            ]
            if word not in whitelist:
                misspelled.append((word, match.context))
    except ltp.utils.LanguageToolError:
        misspelled.append("LT Error")

    return misspelled


def language_tool_grammar_check(lang_tool: ltp.LanguageTool, output_report):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"GRAMMAR"}

    grammar = []

    try:
        matches = lang_tool.check(output_report)
        for match in matches:
            grammar.append(match.ruleId)
    except ltp.utils.LanguageToolError:
        grammar.append("LT Error")

    return grammar


def get_language_tool_metrics(
    responses: Dict[str, Any], lang_tool: ltp.LanguageTool, directories: List[str]
) -> Dict[str, Any]:
    """function to get the language tool metrics"""
    language_tool_metrics = {
        "misspelled": [],
        "grammer": [],
        "other": [],
    }

    for response in responses:
        language_tool_metrics["misspelled"].append(
            language_tool_spelling_check(
                lang_tool, response["raw"]["response"], directories["vocab"]
            )
        )
        language_tool_metrics["grammer"].append(
            language_tool_grammar_check(lang_tool, response["raw"]["response"])
        )

    return language_tool_metrics


# Semantic Metrics
def get_semantic_similarity_llm(model, prompt):
    """function to get the semantic similarity using LLM"""
    response = {}
    try:
        response["raw"] = generate(
            model=model.name + ":" + model.size,
            options=model.options,
            prompt=prompt,
            stream=False,
            context=None,
        )
        try:
            del response["raw"]["context"]
        except KeyError:
            pass
    except ResponseError as e:
        print(e)
        return -1

    try:
        response_value = response["raw"]["response"]
        float_value = float(response_value)
        return float_value
    except (KeyError, ValueError, TypeError):
        print(f"Bad response: {response['raw']}")
        return -1


def get_semantic_similarity_embedding(input_report, output_report):
    """function to get the semantic similarity using embeddings"""
    return 0


def get_semantic_metrics(responses, session, prompt_id=6, model_id=7) -> Dict[str, Any]:
    """function to get the semantic metrics"""
    semantic_metrics = {
        "llm_scores": [],
        "embedding_scores": [],
    }

    model = Models.get_by_id(session, model_id)
    prompt = Prompts.get_by_id(session, prompt_id)

    for response in responses:
        ris = Ris.get_by_id(session, response["ris_id"])
        if ris.revision_1 is not None:
            input_report = ris.revision_1
        elif ris.revision_2 is not None:
            input_report = ris.revision_2
        else:
            continue

        output_report = response["raw"]["response"]

        eval_prompt = (
            prompt.text
            + "\n"
            + "report 1:\n"
            + input_report
            + "\n"
            + "report 2:\n"
            + output_report
        )

        semantic_metrics["llm_scores"].append(
            get_semantic_similarity_llm(model, eval_prompt)
        )
        semantic_metrics["embedding_scores"].append(
            get_semantic_similarity_embedding(input_report, output_report)
        )

    return semantic_metrics


# Eval Functions
def _evaluate(
    generated: Dict[str, Any],
    directories: List[str],
    session: Session,
    lang_tool: ltp.LanguageTool,
    options: Dict[str, bool],
):
    """function to evaluate the performance of the models"""
    # Initialize the metrics
    metrics = {
        "duration_metrics": {
            "load_durations": [],
            "prompt_eval_durations": [],
            "eval_counts": [],
            "eval_durations": [],
            "eval_durations_t/s": [],
        },
        "difference_metrics": {
            "sm_similarity_ratios": [],
            "levenshtein_distances": [],
            "levenshtein_distance_ratios": [],
            "levenshtein_distance_inverse_ratios": [],
        },
        "language_tool_metrics": {"misspelled": [], "grammar": [], "other": []},
        "semantic_metrics": {"llm_scores": [], "embedding_scores": []},
    }

    # Get the metrics
    if options["duration_metrics"]:
        metrics["duration_metrics"] = get_duration_metrics(generated["responses"])
    if options["difference_metrics"]:
        metrics["difference_metrics"] = get_difference_metrics(
            generated["responses"], session
        )
    if options["language_tool_metrics"]:
        metrics["language_tool_metrics"] = get_language_tool_metrics(
            generated["responses"], lang_tool, directories
        )
    if options["semantic_metrics"]:
        metrics["semantic_metrics"] = get_semantic_metrics(
            generated["responses"], session
        )

    # Save the results
    res = {}
    res["model"] = generated["model"]
    res["prompt"] = generated["prompt"]
    res["unique_id"] = generated["unique_id"]
    res["metrics"] = metrics

    # Save the results
    if options["save_json"]:
        save_to_json(
            res,
            os.path.join(directories["evaluations"], f"{generated['unique_id']}.json"),
        )
    # Return the results
    return res


def evaluate_from_unique_ids(
    unique_ids: Union[str, List[str]],
    directories: List[str],
    session: Session,
    lang_tool: ltp.LanguageTool,
    options: Dict[str, bool] = None,
):
    """function to evaluate the performance of the models"""
    if isinstance(unique_ids, str):
        unique_ids = [unique_ids]

    if options is None:
        options = {
            "duration_metrics": True,
            "difference_metrics": True,
            "language_tool_metrics": True,
            "semantic_metrics": True,
            "save_json": True,
        }
    for unique_id in unique_ids:
        file_path = os.path.join(directories["generated"], f"{unique_id}.json")
        with open(file_path, "r", encoding="utf-8") as file:
            responses = json.load(file)

        _evaluate(
            responses,
            directories,
            session,
            lang_tool,
            options,
        )
