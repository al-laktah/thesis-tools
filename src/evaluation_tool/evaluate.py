"""This module contains the functions to evaluate the performance of the models."""

import os
import json
from typing import Any, Dict, List, Union
from difflib import SequenceMatcher
import diff_match_patch as dmp_module
import language_tool_python as ltp
from sqlalchemy.orm import Session
from ollama import ResponseError, generate
from nltk.tokenize import sent_tokenize
from .db import Ris, Models, Prompts, WrongReports, CorrectReports
from .util import save_to_json, get_whitelist


# duration metrics
def get_duration_metrics(responses: Dict[str, Any]) -> Dict[str, Any]:
    """function to get the duration metrics"""
    duration_metrics = {
        "eval_counts": {},
        "eval_durations": {},
        "eval_speeds_t/s": {},
    }

    for response in responses:
        try:
            ris_id = response["ris_id"]
            duration_metrics["eval_counts"].update({ris_id: response["raw"]["eval_count"]})
            duration_metrics["eval_durations"].update({ris_id: response["raw"]["eval_duration"]})
            eval_speed = int(response["raw"]["eval_count"] // (response["raw"]["eval_duration"] / 10**9))
            duration_metrics["eval_speeds_t/s"].update({ris_id: eval_speed})
        except Exception as e:
            print("get_duration_metrics", e)
            continue

    return duration_metrics


# Difference Metrics
def sequencematcher_ratio(input_report, output_report):
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
    responses: Dict[str, Any], session: Session, special: bool = False
) -> Dict[str, Any]:
    """function to get the diffrence metrics"""
    difference_metrics = {
        "sequencematcher_ratios": {},
        "levenshtein_distances": {},
        "levenshtein_distance_ratios": {},
    }

    for response in responses:
        ris_id = response["ris_id"]
        try:
            if special:
                input_report = WrongReports.get_by_id(
                    session, ris_id
                ).befund
            else:
                input_report = Ris.get_by_id(session, ris_id).revision_2

            output_report = response["raw"]["response"]

            difference_metrics["sequencematcher_ratios"].update(
                {ris_id: sequencematcher_ratio(input_report, output_report)}
            )
            distance, ratio = levenshtein_distance_ratio(input_report, output_report)
            difference_metrics["levenshtein_distances"].update({ris_id: distance})
            difference_metrics["levenshtein_distance_ratios"].update({ris_id: ratio})
        except Exception as e:
            print("get_difference_metrics",e)
            continue

    return difference_metrics


# Language Tool Metrics
def language_tool_spelling_check(lang_tool: ltp.LanguageTool, output_report, vocab_dir):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"TYPOS"}

    typos = []
    typos_count = 0
    whitelist_count = 0
    whitelist = get_whitelist(vocab_dir)

    try:
        matches = lang_tool.check(output_report)
        for match in matches:
            try:
                word = match.context[
                    match.offsetInContext : match.offsetInContext + match.errorLength
                ]
                if word in whitelist:
                    whitelist_count += 1
                    typos.append((word, match.context, True))
                else:
                    typos_count += 1
                    typos.append((word, match.context, False))
            except Exception as e:
                print("language_tool_spelling_check", e)
    except ltp.utils.LanguageToolError as e:
        print("language_tool_spelling_check", e)

    return typos, typos_count, whitelist_count


def language_tool_grammar_check(lang_tool: ltp.LanguageTool, output_report):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = True
    lang_tool.enabled_categories = {"GRAMMAR"}

    grammar = []
    count = 0

    try:
        matches = lang_tool.check(output_report)
        count = len(matches)
        for match in matches:
            grammar.append(match.__dict__)
    except ltp.utils.LanguageToolError:
        grammar.append("LT Error")

    return grammar, count

def language_tool_other_check(lang_tool: ltp.LanguageTool, output_report):
    """function to check the output report using language tool"""
    lang_tool.enabled_rules_only = False
    lang_tool.disabled_categories = {"TYPOS", "GRAMMAR"}

    other = []

    try:
        matches = lang_tool.check(output_report)
        for match in matches:
            other.append(match.__dict__)
    except ltp.utils.LanguageToolError:
        other.append("LT Error")

    return other, len(matches)


def get_language_tool_metrics(
    responses: Dict[str, Any], lang_tool: ltp.LanguageTool, directories: List[str]
) -> Dict[str, Any]:
    """function to get the language tool metrics"""
    language_tool_metrics = {
        "counts": {
            "typos": 0,
            "whitelist": 0,
            "grammar": 0,
            "other": 0,
        },
        "typos": {},
        "grammar": {},
        "other": {},
    }

    for response in responses:
        ris_id = response["ris_id"]
        output_report = response["raw"]["response"]

        typos, typos_count, whitelist_count = language_tool_spelling_check(lang_tool, output_report, directories["vocab"])
        language_tool_metrics["counts"]["typos"] += typos_count
        language_tool_metrics["counts"]["whitelist"] += whitelist_count
        language_tool_metrics["typos"].update({ris_id: typos})

        grammar, grammar_count = language_tool_grammar_check(lang_tool, output_report)
        language_tool_metrics["counts"]["grammar"] += grammar_count
        language_tool_metrics["grammar"].update({ris_id: grammar})

        #other, other_count = language_tool_other_check(lang_tool, output_report)
        #language_tool_metrics["counts"]["other"] += other_count
        #language_tool_metrics["other"].update({ris_id: other})



    return language_tool_metrics

# Semantic Metrics
def get_semantic_similarity_llm(model, score_prompt, rating_prompt):
    """function to get the semantic similarity using LLM"""
    response = {}
    score = -1
    rating = -1
    # Get the score
    for _ in range(3):
        try:
            response["score"] = generate(
                model=model.name + ":" + model.size,
                options=model.options,
                prompt=score_prompt,
                stream=False,
                context=None,
            )
            try:
                del response["score"]["context"]
            except KeyError:
                pass
        except ResponseError:
            continue

        try:
            response_value = response["score"]["response"]
            score = float(response_value)
            break
        except (KeyError, ValueError, TypeError):
            score = -1
            continue

    # Get the rating
    for _ in range(3):
        try:
            response["rating"] = generate(
                model=model.name + ":" + model.size,
                options=model.options,
                prompt=rating_prompt,
                stream=False,
                context=None,
            )
            try:
                del response["rating"]["context"]
            except KeyError:
                pass
        except ResponseError:
            continue

        try:
            response_value = response["rating"]["response"]
            rating = int(response_value)
            break
        except (KeyError, ValueError, TypeError):
            rating = -1
            continue

    return score, rating


def get_semantic_similarity_embedding(model1, model2, input_report, output_report, correct_report):
    """function to get the semantic similarity using embeddings"""
    scores = {
        "input_output": {
            "whole": (0.0, 0.0),
            "sentences": ([],[]),
        },
        "input_correct": {
            "whole": (0.0, 0.0),
            "sentences": ([],[]),
        },
    }

    input_sentences = sent_tokenize(input_report)
    output_sentences = sent_tokenize(output_report)
    correct_sentences = sent_tokenize(correct_report)

    # Get the embeddings for the whole reports
    try:
        whole_embeddings1 = model1.encode([input_report, output_report, correct_report], normalize_embeddings=True)
        whole_embeddings2 = model2.encode([input_report, output_report, correct_report], normalize_embeddings=True)
        scores["input_output"]["whole"] = (float(whole_embeddings1[0] @ whole_embeddings1[1]), float(whole_embeddings2[0] @ whole_embeddings2[1]))
        scores["input_correct"]["whole"] = (float(whole_embeddings1[0] @ whole_embeddings1[2]), float(whole_embeddings2[0] @ whole_embeddings2[2]))
    except Exception as e:
        print("get_semantic_similarity_embedding", e)

    # Get the embeddings for the sentences
    try:
        sentences_embeddings1 = model1.encode(
            input_sentences + output_sentences + correct_sentences,
            normalize_embeddings=True
        )

        sentences_embeddings2 = model2.encode(
            input_sentences + output_sentences + correct_sentences,
            normalize_embeddings=True
        )

        input_embeddings1 = sentences_embeddings1[:len(input_sentences)]
        output_embeddings1 = sentences_embeddings1[len(input_sentences):len(input_sentences) + len(output_sentences)]
        correct_embeddings1 = sentences_embeddings1[len(input_sentences) + len(output_sentences):]

        input_embeddings2 = sentences_embeddings2[:len(input_sentences)]
        output_embeddings2 = sentences_embeddings2[len(input_sentences):len(input_sentences) + len(output_sentences)]
        correct_embeddings2 = sentences_embeddings2[len(input_sentences) + len(output_sentences):]
        
        scores["input_output"]["sentences"] = (
            [float(input_embeddings1[i] @ output_embeddings1[i]) for i in range(min(len(input_sentences), len(output_sentences)))],
            [float(input_embeddings2[i] @ output_embeddings2[i]) for i in range(min(len(input_sentences), len(output_sentences)))]
        )

        scores["input_correct"]["sentences"] = (
            [float(input_embeddings1[i] @ correct_embeddings1[i]) for i in range(min(len(input_sentences), len(correct_sentences)))],
            [float(input_embeddings2[i] @ correct_embeddings2[i]) for i in range(min(len(input_sentences), len(correct_sentences)))]
        )
    except Exception as e:
        print("get_semantic_similarity_embedding", e)

    return scores


def get_semantic_metrics(
    responses,
    session,
    model1,
    model2,
    scores_prompt_id=6,
    ratings_prompt_id=12,
    model_id=7,
    special: bool = False,
) -> Dict[str, Any]:
    """function to get the semantic metrics"""
    semantic_metrics = {
        "llm_scores": {
            "fails": [],
        },
        "llm_ratings": {
            "fails": [],
        },
        "embedding_scores": {},
    }

    model = Models.get_by_id(session, model_id)
    scores_prompt = Prompts.get_by_id(session, scores_prompt_id)
    ratings_prompt = Prompts.get_by_id(session, ratings_prompt_id)

    for response in responses:
        ris_id = response["ris_id"]
        try:
            if special:
                input_report = WrongReports.get_by_id(session, ris_id).befund
                correct_report = CorrectReports.get_by_ris_id(session, ris_id).befund
            else:
                input_report = Ris.get_by_id(session, ris_id).revision_2
                correct_report = Ris.get_by_id(session, ris_id).final

            output_report = response["raw"]["response"]

            eval_prompt_score = (
                scores_prompt.text
                + "\n"
                + "report 1:\n"
                + input_report
                + "\n"
                + "report 2:\n"
                + output_report
            )

            eval_prompt_rating = (
                ratings_prompt.text
                + "\n"
                + "report 1:\n"
                + input_report
                + "\n"
                + "report 2:\n"
                + output_report
            )

            score, rating = get_semantic_similarity_llm(model, eval_prompt_score, eval_prompt_rating)

            if score == -1:
                semantic_metrics["llm_scores"]["fails"].append(ris_id)
            else:
                semantic_metrics["llm_scores"].update({ris_id: score})

            if rating == -1:
                semantic_metrics["llm_ratings"]["fails"].append(ris_id)
            else:
                semantic_metrics["llm_ratings"].update({ris_id: rating})

            semantic_metrics["embedding_scores"].update({ris_id: get_semantic_similarity_embedding(model1, model2, input_report, output_report, correct_report)})
        except Exception as e:
            print("get_semantic_similarity_embedding", e)
            continue

    return semantic_metrics


# Eval Functions
def _evaluate(
    generated: Dict[str, Any],
    directories: List[str],
    session: Session,
    lang_tool: Union[ltp.LanguageTool, None],
    model1,
    model2,
    options: Dict[str, bool],
    update: bool,
):
    """function to evaluate the performance of the models"""
    # Initialize the metrics
    metrics = {
        "duration_metrics": {},
        "difference_metrics": {},
        "language_tool_metrics": {},
        "semantic_metrics": {},
    }

    special = generated["prompt"]["id"] not in [4, 5]

    print(f"Evaluating {generated['model']['name']}:{generated['model']['size']} with prompt {generated['prompt']['id']}")

    # Get the metrics
    if options["duration_metrics"] and generated["prompt"]["id"] != 0:
        metrics["duration_metrics"] = get_duration_metrics(generated["responses"])
    if options["difference_metrics"]:
        metrics["difference_metrics"] = get_difference_metrics(
            generated["responses"], session, special=special
        )
    if options["language_tool_metrics"]:
        metrics["language_tool_metrics"] = get_language_tool_metrics(
            generated["responses"], lang_tool, directories
        )
    if options["semantic_metrics"]:
        metrics["semantic_metrics"] = get_semantic_metrics(
            generated["responses"], session, model1, model2, special=special
        )

    # Save the results
    res = {}
    res["model"] = generated["model"]
    res["prompt"] = generated["prompt"]
    res["unique_id"] = generated["unique_id"]
    res["metrics"] = metrics

    # Save the results
    if options["save_json"]:
        if update:
            save_to_json(
                res,
                os.path.join(
                    directories["evaluations"], f"update_{generated['unique_id']}.json"
                ),
            )
        else:
            save_to_json(
                res,
                os.path.join(
                    directories["evaluations"], f"{generated['unique_id']}.json"
                ),
            )
    # Return the results
    return res


def evaluate_from_unique_ids(
    unique_ids: Union[str, List[str]],
    directories: List[str],
    session: Session,
    lang_tool: Union[ltp.LanguageTool, None],
    model1,
    model2,
    options: Dict[str, bool] = None,
    update: bool = False,
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
    else:
        options = {
            "duration_metrics": 1 in options,
            "difference_metrics": 2 in options,
            "language_tool_metrics": 3 in options,
            "semantic_metrics": 4 in options,
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
            model1,
            model2,
            options=options,
            update=update,
        )
