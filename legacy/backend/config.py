EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Parameters passed to the LLM
# model_name: either "gpt-4" or "gpt-3.5-turbo"
OPENAI_PARAMS = {"model_name": "gpt-3.5-turbo", "temperature": 0, "max_tokens": 256}

# Token the LLM shall return if given context does not contain answer to the question,
# used in non_answer_handling.py and PROMPTS
NON_ANSWER_TOKEN = "<NOT FOUND>"

# Examples of answers the LLM might return instead of the NON_ANSWER_TOKEN, used in non_answer_handling.py
NON_ANSWER_EXAMPLES = [
    "The given context does not",
    "The passage does not",
    "The given text does not",
    "The context does not",
]

# Prompt template for the LLM, {question} and {context} will be replaced by user input
# SYSTEM: Prompt for the LLM to explain its purpose, NON_ANSWER_TOKEN and tone
# HUMAN: Input from the user
PROMPTS = {
    "SYSTEM": f"You are a highly intelligent question answering bot. You take Question and Context as input and return the answer from the Paragraph. Retain as much information as needed to answer the question at a later time. The answer must only address the question. Use a descriptive and objective tone. If Context lacks the answer you must only return '{NON_ANSWER_TOKEN}', nothing else.",
    "HUMAN": "Question: \n```{question}```\n\nContext: \n```{context}```",
}
