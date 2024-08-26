import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.compute import generate_from
from src.db import Ris


engine = create_engine('sqlite:///DB.db')
Session = sessionmaker(bind=engine)
session = Session()

data = Ris.get_rev_reports(session)

unique_id, responses, log = generate_from(1, 4, session, data)

# Write responses to a JSON file
with open(f'{unique_id}_responses.json', 'w', encoding='utf-8') as responses_file:
    json.dump(responses, responses_file, indent=4)

# Write log to a JSON file
with open(f'{unique_id}_log.json', 'w', encoding='utf-8') as log_file:
    json.dump(log, log_file, indent=4, ensure_ascii=False)
    
    
print(f"Done! Check the files {unique_id}_responses.json and {unique_id}_log.json")