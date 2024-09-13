"""This module contains the functions to evaluate the performance of the models."""

import os
import json
from typing import Any, Dict, List, Union
from difflib import SequenceMatcher
import diff_match_patch as dmp_module
import language_tool_python as ltp
from sqlalchemy.orm import Session
from .db import Ris
from .util import save_to_json, dump_raw, get_whitelist


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

    for response in responses["responses"]:
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

    for response in responses["responses"]:
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


# Language Tool Metrics
def language_tool_spelling_check(lang_tool: ltp.LanguageTool, output_report, vocab_dir):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"TYPOS"}

    matches = lang_tool.check(output_report)
    whitelist = get_whitelist(vocab_dir)

    misspelled = []

    for match in matches:
        word = match.context[
            match.offsetInContext : match.offsetInContext + match.errorLength
        ]

        if word not in whitelist:
            misspelled.append(word)

    return misspelled


def language_tool_grammer_check(lang_tool: ltp.LanguageTool, output_report):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"GRAMMAR"}

    matches = lang_tool.check(output_report)

    grammer = []

    for match in matches:
        grammer.append(match)

    return grammer


def get_language_tool_metrics(
    responses: Dict[str, Any], lang_tool: ltp.LanguageTool, directories: List[str]
) -> Dict[str, Any]:
    """function to get the language tool metrics"""
    language_tool_metrics = {
        "misspelled": [],
        "grammer": [],
        "other": [],
    }

    for response in responses["responses"]:
        language_tool_metrics["misspelled"].append(
            language_tool_spelling_check(
                lang_tool, response["raw"]["response"], directories["vocab"]
            )
        )
        language_tool_metrics["grammer"].append(
            language_tool_grammer_check(lang_tool, response["raw"]["response"])
        )

    return language_tool_metrics


def _evaluate(
    responses: Dict[str, Any],
    unique_id: str,
    directories: List[str],
    session: Session,
    lang_tool: ltp.LanguageTool,
    options: Dict[str, bool],
):
    """function to evaluate the performance of the models"""

    metrics = {}
    if options["difference_metrics"]:
        metrics["difference_metrics"] = get_difference_metrics(responses, session)
    if options["language_tool_metrics"]:
        metrics["language_tool_metrics"] = get_language_tool_metrics(
            responses, lang_tool, directories
        )
    if options["duration_metrics"]:
        metrics["duration_metrics"] = get_duration_metrics(responses)

    res = {
        "model": responses["model"],
        "prompt": responses["prompt"],
        "unique_id": unique_id,
        "metrics": metrics,
    }

    if options["save_json"]:
        try:
            save_to_json(
                res, os.path.join(directories["evaluations"], f"{unique_id}.json")
            )
        except TypeError as e:
            dump_raw(
                res,
                os.path.join(directories["evaluations"], f"failed_{unique_id}.txt"),
            )
            print(e)
            print(
                f"Error saving evaluation for {responses['model']} & {responses['prompt']} as json."
            )
        finally:
            print(f"Finished Evaluation, uid: {unique_id}")

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
            "save_json": True,
            "difference_metrics": True,
            "duration_metrics": True,
            "language_tool_metrics": True,
        }
    for unique_id in unique_ids:
        file_path = os.path.join(directories["generated"], f"{unique_id}.json")
        with open(file_path, "r", encoding="utf-8") as file:
            responses = json.load(file)

        _evaluate(
            responses,
            unique_id,
            directories,
            session,
            lang_tool,
            options,
        )
