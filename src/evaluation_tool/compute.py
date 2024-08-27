"""Module containing functions to generate and evaluate model outputs."""

from uuid import uuid4
from typing import Optional, List
from ollama import ResponseError, generate
from pandas import DataFrame
from sqlalchemy.orm import Session

from .db import Models, Prompts, Ris


def _generate_from(model, prompt, data):
    """Generate outputs from given model, prompt, and data."""

    unique_id = str(uuid4())
    responses = []
    log = {}

    for _, row in data.iterrows():
        ris_id = row["id"]
        text = row["report"]

        response = {"ris_id": ris_id}

        try:
            response["raw"] = generate(
                model=model.name + ":" + model.size,
                options=model.options,
                prompt=prompt.prompt + "\n" + text,
                stream=False,
                context=None,
            )
        except ResponseError as e:
            response["raw"] = {
                "error": "An error occurred, consult the log for more information"
            }
            log[ris_id] = e
        finally:
            responses.append(response)

    if log:
        return unique_id, responses, log
    return unique_id, responses, None


def generate_from(
    model_ids: List[int],
    prompt_ids: List[int],
    session: Optional[Session] = None,
    data: Optional[DataFrame] = None,
):
    """Generate outputs from given models, prompts, and data."""
    results = {}

    if data is None:
        data = Ris.get_rev_reports(session)

    for model_id in model_ids:
        model = Models.get_by_id(session, model_id)

        for prompt_id in prompt_ids:
            prompt = Prompts.get_by_id(session, prompt_id)

            unique_id, responses, log = _generate_from(model, prompt, data)

            results[unique_id] = {
                "model": str(model),
                "prompt": str(prompt),
                "responses": responses,
                "log": log,
            }

    return results
