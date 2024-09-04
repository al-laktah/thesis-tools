"""This module contains the functions to evaluate the performance of the models."""

import os
import json
from typing import Any, Dict, List
from difflib import SequenceMatcher
import diff_match_patch as dmp_module
import language_tool_python as ltp
from sqlalchemy.orm import Session
from .compute import _generate_from
from .db import Ris
from .util import save_to_json


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


def language_tool_check(lang_tool, output_report, whitelist=None):
    """function to check the output report using language tool"""
    matches = lang_tool.check(output_report)

    misspelled = []
    grammer = []
    other = []

    for match in matches:
        if match.ruleId == "GERMAN_SPELLER_RULE":
            word = match.context[
                match.offsetInContext : match.offsetInContext + match.errorLength
            ]
            if whitelist and word in whitelist:
                continue
            misspelled.append(word)
        elif match.ruleId == "GERMAN_GRAMMAR_RULE":
            grammer.append(match)
        else:
            other.append(match)

    return misspelled, grammer, other


def _evaluate(
    responses: Dict[str, Any],
    unique_id: str,
    evaluations_dir: str,
    session: Session,
    lang_tool: ltp.LanguageTool,
    whitelist: List = None,
    save_json: bool = False,
):
    """function to evaluate the performance of the models"""

    metrics = {
        "sm_similarity_ratios": [],
        "levenshtein_distances": [],
        "levenshtein_distance_ratios": [],
        "levenshtein_distance_inverse_ratios": [],
        "durations": {
            "load_durations": [],
            "prompt_eval_durations": [],
            "eval_counts": [],
            "eval_durations": [],
            "eval_durations_t/s": [],
        },
        "language_tool": {
            "misspelled": [],
            "grammer": [],
            "other": [],
        },
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

        # Duration metrics
        metrics["durations"]["load_durations"].append(response["raw"]["load_duration"])
        metrics["durations"]["prompt_eval_durations"].append(
            response["raw"]["prompt_eval_duration"]
        )
        metrics["durations"]["eval_counts"].append(response["raw"]["eval_count"])
        metrics["durations"]["eval_durations"].append(response["raw"]["eval_duration"])
        # calculate how fast the response is generated in tokens per second (token/s)
        metrics["durations"]["eval_durations_t/s"].append(
            int(
                response["raw"]["eval_count"]
                // (response["raw"]["eval_duration"] / 10**9)
            )
        )

        # Diff Metrics
        metrics["sm_similarity_ratios"].append(
            sm_similarity_ratio(input_report, output_report)
        )
        distance, ratio = levenshtein_distance_ratio(input_report, output_report)
        metrics["levenshtein_distances"].append(distance)
        metrics["levenshtein_distance_ratios"].append(ratio)
        metrics["levenshtein_distance_inverse_ratios"].append(1 - ratio)

        # Language Tool Metrics
        misspelled, grammer, other = language_tool_check(
            lang_tool, output_report, whitelist
        )
        metrics["language_tool"]["misspelled"].append(misspelled)
        metrics["language_tool"]["grammer"].append(grammer)
        metrics["language_tool"]["other"].append(other)

    res = {
        "model": responses["model"],
        "prompt": responses["prompt"],
        "unique_id": unique_id,
        "metrics": metrics,
    }

    if save_json:
        save_to_json(res, os.path.join(evaluations_dir, f"{unique_id}.json"))

    return res


def evaluate_from_model(
    model_id: int,
    prompt_id: int,
    evaluations_dir: str,
    session: Session,
    lang_tool: ltp.LanguageTool,
    save_json: bool = False,
) -> None:
    """function to evaluate the performance of the models"""

    unique_id, responses, log = _generate_from(model_id, prompt_id, session)

    if log:
        print("error occurred during generation")
        return log

    return _evaluate(
        responses, unique_id, evaluations_dir, session, lang_tool, save_json
    )


def evaluate_from_unique_id(
    unique_id: str,
    responses_dir: str,
    evaluations_dir: str,
    session: Session,
    lang_tool: ltp.LanguageTool,
    save_json: bool = False,
):
    """function to evaluate the performance of the models"""

    file_path = os.path.join(responses_dir, f"{unique_id}.json")
    with open(file_path, "r", encoding="utf-8") as file:
        responses = json.load(file)

    if save_json:
        return True
    return _evaluate(
        responses, unique_id, evaluations_dir, session, lang_tool, save_json
    )
