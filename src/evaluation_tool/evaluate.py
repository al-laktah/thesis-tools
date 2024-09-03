"""This module contains the functions to evaluate the performance of the models."""

import os
import json
from typing import Any, Dict
from difflib import SequenceMatcher
import diff_match_patch as dmp_module
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


def _evaluate(
    responses: Dict[str, Any],
    unique_id: str,
    evaluations_dir: str,
    session: Session,
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

        metrics["durations"]["load_durations"].append(response["raw"]["load_duration"])
        metrics["durations"]["prompt_eval_durations"].append(
            response["raw"]["prompt_eval_duration"]
        )
        metrics["durations"]["eval_counts"].append(response["raw"]["eval_count"])
        metrics["durations"]["eval_durations"].append(response["raw"]["eval_duration"])
        # calculate how fast the response is generated in tokens per second (token/s)
        metrics["durations"]["eval_durations_t/s"].append(
            int(response["raw"]["eval_count"] // (response["raw"]["eval_duration"] / 10**9))
        )

        metrics["sm_similarity_ratios"].append(
            sm_similarity_ratio(input_report, output_report)
        )

        distance, ratio = levenshtein_distance_ratio(input_report, output_report)
        metrics["levenshtein_distances"].append(distance)
        metrics["levenshtein_distance_ratios"].append(ratio)
        metrics["levenshtein_distance_inverse_ratios"].append(1 - ratio)

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
    save_json: bool = False,
) -> None:
    """function to evaluate the performance of the models"""

    unique_id, responses, log = _generate_from(model_id, prompt_id, session)

    if log:
        print("error occurred during generation")
        return log

    return _evaluate(responses, unique_id, evaluations_dir, session, save_json)


def evaluate_from_unique_id(
    unique_id: str,
    responses_dir: str,
    evaluations_dir: str,
    session: Session,
    save_json: bool = False,
):
    """function to evaluate the performance of the models"""

    file_path = os.path.join(responses_dir, f"{unique_id}.json")
    with open(file_path, "r", encoding="utf-8") as file:
        responses = json.load(file)

    return _evaluate(responses, unique_id, evaluations_dir, session, save_json)
