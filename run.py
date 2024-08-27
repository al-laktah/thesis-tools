"""file to run the program"""

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.compute import generate_from
from src.db import Ris


engine = create_engine("sqlite:///data/DB.db")
Session = sessionmaker(bind=engine)
session = Session()

data = Ris.get_rev_reports(session)

for model_id in [1, 5, 7, 8, 9, 12, 14]:
    unique_id, responses, log = generate_from(model_id, 4, session, data)

    # Write responses to a JSON file
    with open(
        f"data/generated/{unique_id}_responses.json", "w", encoding="utf-8"
    ) as responses_file:
        json.dump(responses, responses_file, indent=4, ensure_ascii=False)

    # Write log to a JSON file
    if log:
        with open(f"data/logs/{unique_id}_log.json", "w", encoding="utf-8") as log_file:
            json.dump(log, log_file, indent=4, ensure_ascii=False)

        print(
            f"Done! Check the files {unique_id}_responses.json and {unique_id}_log.json"
        )
    else:
        print(f"Done! Check the file {unique_id}_responses.json")
