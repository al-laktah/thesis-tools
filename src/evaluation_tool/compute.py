"""Module containing functions to generate and evaluate model outputs."""

import os
from uuid import uuid4
from typing import List
from ollama import ResponseError, generate
from sqlalchemy.orm import Session

from .db import Models, Prompts, Ris
from .util import save_to_json, dump_raw


def _generate_from(model, prompt, data):
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
                prompt=prompt.prompt + "\n" + text,
                stream=False,
                context=None,
            )
        except ResponseError as e:
            response["raw"] = {
                "error": "An error occurred, consult the log for more information"
            }
            log[ris_id] = str(e)
            print(f"Error: {index}")
        finally:
            responses.append(response)

        if index % 25 == 0 and index != 0:
            print(f"Generated {index} outputs...")

    return unique_id, responses, log


def generate_from(
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
            unique_id, responses, log = _generate_from(model, prompt, data)

            generated_responses = {
                "model": str(model),
                "prompt": str(prompt),
                "unique_id": unique_id,
                "responses": responses,
            }

            try:
                save_to_json(
                    generated_responses,
                    os.path.join(responses_dir, f"{unique_id}.json"),
                )
            except TypeError as e:
                dump_raw(
                    generated_responses,
                    os.path.join(responses_dir, f"failed_{unique_id}.txt"),
                )
                print(e)
                print(
                    f"Error saving responses for model {model} and prompt {prompt} as json: dumped raw responses instead."
                )
            finally:
                print(f"Finished, uid: {unique_id}")

            if log:
                generated_log = {
                    "model": str(model),
                    "prompt": str(prompt),
                    "unique_id": unique_id,
                    "log": log,
                }
                try:
                    save_to_json(
                        generated_log, os.path.join(log_dir, f"{unique_id}.json")
                    )
                except TypeError as e:
                    dump_raw(
                        generated_log,
                        os.path.join(log_dir, f"failed_{unique_id}.txt"),
                    )
                    print(e)
                    print(
                        f"Error saving log for model {model} and prompt {prompt} as json: dumped raw log instead."
                    )
