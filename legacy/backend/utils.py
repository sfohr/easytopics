import tiktoken
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_PRICING = {
  "gpt-3.5-turbo-0613": {
    "prompt": 0.0015,
    "completion": 0.002,
    "max_tokens": 4097
  }
}

class OpenAICashier():
  def __init__(self, system_prompt: str, max_completion_token_length: int, model: str="gpt-3.5-turbo-0613") -> None:
    self.api_pricing = MODEL_PRICING[model]
    self.encoding = tiktoken.encoding_for_model(model)
    self.system_prompt = system_prompt
    self.system_prompt_ntokens = self.count_tokens(self.system_prompt)
    self.system_prompt_cost = self._calculate_cost(ntokens=self.system_prompt_ntokens, type="prompt")
    self.max_completion_token_length = max_completion_token_length
    self.max_completion_cost = self._calculate_cost(ntokens=self.max_completion_cost, type="completion")

  def count_tokens(self, x: str) -> int:
    # check for tests: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    num_tokens = len(self.encoding.encode(x))
    return num_tokens
    
  def _calculate_cost(self, ntokens: int, type: str) -> float:
    assert type in ["prompt", "completion"]
    cost = self.api_pricing[type]
    return ntokens / 1000. * cost
    
  def calculate_max_cost(self, context: str, question: str) -> float:
    cost = self.system_prompt_cost + self.max_completion_cost
    ntokens = self.count_tokens(question)
    cost += self._calculate_cost(ntokens=ntokens, type="prompt")
    return cost
  

def check_non_answers(answers: list[str]) -> list[bool]:
    """Checks if answers are a non-answer

    Args:
        answers: list of strings containing the answers

    Returns:
        True if the answer is a non-answer
    """
    #has_not_found = "NOT FOUND" in answer | "not found" in answer

    NONE_ANSWERS = [
        "The given context does not",
        "The passage does not",
        "The given text does not",
        "The context does not"
    ]
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # crop answers to 100 chars
    cropped_answers = [answer[:100] for answer in answers if len(answer) > 200]

    embeddings = embedder.encode(cropped_answers, normalize_embeddings=True)
    embeddings_none_answers = embedder.encode(NONE_ANSWERS, normalize_embeddings=True)

    # calculate centroid of none answers
    centroid = np.mean(embeddings_none_answers, axis=0)

    # calculate cosine similarity between centroid and embeddings
    similarities = np.dot(embeddings, centroid)

    # if the similarity is above 0.8, it is a non-answer
    return list[similarities > 0.1]