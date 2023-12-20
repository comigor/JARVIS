from simpleaichat import AIChat
from pydantic import BaseModel, Field
from simpleaichat.utils import wikipedia_search, wikipedia_search_lookup
import os

model = 'thebloke__open-llama-7b-open-instruct-ggml__open-llama-7b-open-instruct.ggmlv3.q4_0.bin'
# model = 'thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf'

# This uses the Wikipedia Search API.
# Results from it are nondeterministic, your mileage will vary.
def search(query):
    """Search the internet."""
    print('aaaaaaaaaaaaaaaaaaaaaaaa')
    wiki_matches = wikipedia_search(query, n=3)
    return {"context": ", ".join(wiki_matches), "titles": wiki_matches}

def lookup(query):
    """Lookup more information about a topic."""
    print('bbbbbbbbbbbbbbbbbbbbbb')
    page = wikipedia_search_lookup(query, sentences=3)
    return page

params = {"temperature": 0.0, "max_tokens": 100}
ai = AIChat(
    api_key=os.getenv("OPENAI_API_KEY"),
    api_url='http://127.0.0.1:8080/v1/chat/completions',
    model=model,
    params=params,
    console=False
)

print(ai("San Francisco tourist attractions", tools=[search, lookup]))
