import openai
import instructor
from pydantic import BaseModel, field_validator

# Apply the patch to the OpenAI client
instructor.patch()

openai.api_base = 'http://127.0.0.1:8080/v1'
model = 'thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf'

class UserDetails(BaseModel):
    name: str
    age: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v.upper() != v:
            raise ValueError("Name must be in uppercase.")
        return v

model = openai.ChatCompletion.create(
    model=model,
    response_model=UserDetails,
    max_retries=2,
    messages=[
        {"role": "user", "content": "hello"},
    ],
)

print(model)

assert model.name == "JASON"

# only function calls!
