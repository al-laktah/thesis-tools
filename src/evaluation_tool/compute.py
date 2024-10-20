"""Module containing functions to generate and evaluate model outputs."""

import os
from uuid import uuid4
from typing import List
from ollama import ResponseError, generate
from sqlalchemy.orm import Session

from .db import Models, Prompts, Ris, WrongReports
from .util import save_to_json
from .prompts import prompt_eight, prompt_nine, prompt_ten, prompt_eleven


def _generate_all(model, prompt, data):
    """Generate outputs from given model, prompt, and data."""

    unique_id = str(uuid4())
    responses = []
    log = {}

    for index, row in data.iterrows():
        ris_id = row["id"]
        text = row["report"]

        response = {"ris_id": ris_id}

        try:
            response["raw"] = generate(
                model=model.name + ":" + model.size,
                options=model.options,
                prompt=prompt.text + "\n" + text,
                stream=False,
                context=None,
            )
            try:
                del response["raw"]["context"]
            except KeyError:
                pass
        except ResponseError as e:
            response["raw"] = {
                "error": "An error occurred, consult the log for more information"
            }
            log[ris_id] = str(e)
            print(f"Error: {index}")
        finally:
            responses.append(response)

        print(f"Generated {index} / 207 Reports...")

    return unique_id, responses, log


def generate_all_from(
    model_ids: List[int],
    prompt_ids: List[int],
    responses_dir: str,
    log_dir: str,
    session: Session,
) -> None:
    """Generate outputs from given models and prompts"""

    data = Ris.get_rev_reports(session)

    for model_id in model_ids:
        model = Models.get_by_id(session, model_id)

        for prompt_id in prompt_ids:
            prompt = Prompts.get_by_id(session, prompt_id)

            print(f"Generating from model {model} using prompt {prompt.id}...")
            unique_id, responses, log = _generate_all(model, prompt, data)

            unique_id = f"{model.short_name}-{model_id}-{prompt.id}.{unique_id}"
            generated_responses = {
                "model": {
                    "id": model_id,
                    "name": model.name,
                    "size": model.size,
                    "options": model.options,
                    "family": model.family,
                    "short_name": model.short_name,
                },
                "prompt": {
                    "id": prompt_id,
                    "text": prompt.text,
                    "tags": prompt.tags,
                },
                "unique_id": unique_id,
                "responses": responses,
            }
            generated_log = {
                "model": {
                    "id": model_id,
                    "name": model.name,
                    "size": model.size,
                    "options": model.options,
                    "family": model.family,
                    "short_name": model.short_name,
                },
                "prompt": {
                    "id": prompt_id,
                    "text": prompt.text,
                    "tags": prompt.tags,
                },
                "unique_id": unique_id,
                "log": log,
            }

            if not save_to_json(
                generated_responses, os.path.join(responses_dir, f"{unique_id}.json")
            ):
                print(
                    f"Error saving responses for {model} and {prompt}, printing instead:"
                )
                print(generated_responses)

            if not save_to_json(
                generated_log, os.path.join(log_dir, f"{unique_id}.json")
            ):
                print(f"Error saving log for {model} and {prompt}, printing instead:")
                print(generated_log)

def generat_one(model, prompt):
    """Generate outputs from given model, prompt, and data."""

    response = {}

    try:
        response = generate(
            model=model.name + ":" + model.size,
            options=model.options,
            prompt=prompt,
            stream=False,
            context=None,
        )
        try:
            del response["context"]
        except KeyError:
            pass
    except ResponseError as e:
        print(e)
        response = {
            "error": "An error occurred, consult the log for more information"
        }

    return response

def generate_all_special(
    model_ids: List[int],
    prompt_id: int,
    responses_dir: str,
    session: Session,
) -> None:
    """Generate outputs from given models and prompts"""

    data = WrongReports.get_all(session)

    for model_id in model_ids:
        model = Models.get_by_id(session, model_id)

        print(f"Generating from model {model} using speical prompt...")
        unique_id = str(uuid4())
        unique_id = f"{model.short_name}-{model_id}-{prompt_id}.{unique_id}"
        responses = []

        for index, row in data.iterrows():
            ris_id = row["id"]
            report = {
                "klinische_angaben": row["klinische_angaben"],
                "fragestellung": row["fragestellung"],
                "methodik": row["methodik"],
                "befund": row["befund"],
                "beurteilung": row["beurteilung"],
            }
            prompt = prompt_switcher(prompt_id, report)

            response = {"ris_id": ris_id}
            response["prompt"] = prompt
            try:
                response["raw"] = generat_one(model, prompt)
                try:
                    del response["raw"]["context"]
                except KeyError:
                    pass
            except ResponseError as e:
                response["raw"] = {
                    "error": f"{e}"
                }
            finally:
                responses.append(response)

            print(f"Generated {index} / 207 Reports...")

        generated_responses = {
            "model": {
                "id": model_id,
                "name": model.name,
                "size": model.size,
                "options": model.options,
                "family": model.family,
                "short_name": model.short_name,
            },
            "prompt": {
                "id": prompt_id,
                "text": f"speical prompt: {prompt_id}",
                "tags": ["special"],
            },
            "unique_id": unique_id,
            "responses": responses,
        }
        if not save_to_json(
            generated_responses, os.path.join(responses_dir, f"{unique_id}.json")
        ):
            print(
                f"Error saving responses for {model} and prompt: {prompt_id}, printing instead:"
            )
            print(generated_responses)

def prompt_switcher(prompt_id, report):
    """Switcher function to return the correct prompt based on the prompt_id."""
    match prompt_id:
        case 8:
            return prompt_eight(report)
        case 9:
            return prompt_nine(report)
        case 10:
            return prompt_ten(report)
        case 11:
            return prompt_eleven(report)
        case _:
            raise ValueError(f"Invalid prompt_id: {prompt_id}")
