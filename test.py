import os
from dotenv import load_dotenv

load_dotenv()
exa_api_key = os.getenv('EXA_API_KEY')

from exa_py import Exa
exa = Exa('exa_api_key')

results = exa.search_and_contents(
    "AI blogs", 
    text=False
)

print(results)