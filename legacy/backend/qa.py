import os
from config import (
    OPENAI_PARAMS,
    PROMPTS,
    EMBEDDING_MODEL,
    NON_ANSWER_TOKEN,
    NON_ANSWER_EXAMPLES,
)
from sentence_transformers import SentenceTransformer, util
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_ORG = os.getenv("OPENAI_ORG")

TEMPLATE = ChatPromptTemplate.from_messages(
    [("system", PROMPTS["SYSTEM"]), ("human", PROMPTS["HUMAN"])]
)


class QAProcessor:
    def __init__(
        self,
        key: str = OPENAI_KEY,
        org: str = OPENAI_ORG,
        prompt_template: ChatPromptTemplate = TEMPLATE,
        non_answer_token: str = NON_ANSWER_TOKEN,
        non_answer_examples: list[str] = NON_ANSWER_EXAMPLES,
        embedding_model: SentenceTransformer = SentenceTransformer(EMBEDDING_MODEL),
    ) -> None:
        """_summary_

        Args:
            key (str, optional): _description_. Defaults to OPENAI_KEY.
            org (str, optional): _description_. Defaults to OPENAI_ORG.
            prompt_template (ChatPromptTemplate, optional): _description_. Defaults to TEMPLATE.
            non_answer_token (str, optional): _description_. Defaults to NON_ANSWER_TOKEN.
            non_answer_examples (list[str], optional): _description_. Defaults to NON_ANSWER_EXAMPLES.
            embedding_model (SentenceTransformer, optional): _description_. Defaults to SentenceTransformer(EMBEDDING_MODEL).
        """
        self.llm = ChatOpenAI(
            openai_api_key=key,
            openai_organization=org,
            max_tokens=OPENAI_PARAMS["max_tokens"],
            temperature=OPENAI_PARAMS["temperature"],
            model_name=OPENAI_PARAMS["model_name"],
        )
        self.embedding_model = embedding_model
        self.prompt_template = prompt_template
        self.non_answer_token = non_answer_token
        self.non_answers_embedded = self.embedding_model.encode(
            non_answer_examples, normalize_embeddings=True
        )

    def _ask_question_to_txt(
        self, question: str, context: str, debug: bool = False
    ) -> str:
        """Ask OpenAI LLM a question given a context and return the answer

        Args:
            question (str): the question asked to the LLM
            context (str): the context for the question
            debug (bool, optional): For debugging and testing purposes, returns context with calling the LLM. Defaults to False.

        Returns:
            str: the LLMs response
        """
        msg = self.prompt_template.format_messages(question=question, context=context)

        if debug:
            return context
        response = self.llm(messages=msg)
        return response.content

    def ask_question_to_texts(
        self, question: str, texts: list[str], debug: bool = False
    ) -> list[str]:
        answers = []
        for text in texts:
            answers.append(self._ask_question_to_txt(question, text, debug))
        # is_non_answer = self.check_non_answers(answers)
        # answers_cleaned = []
        # for answer, is_non in zip(answers, is_non_answer):
        #     if is_non:
        #         answers_cleaned.append(self.non_answer_token)
        #     else:
        #         answers_cleaned.append(answer)
        return answers

    def check_non_answers(
        self,
        answers: list[str],
        threshold: float = 0.3,
    ) -> list[bool]:
        """Checks if answers from LLM are non-answers

        Non-answers are responses in which the LLM states that the answer cannot be found in the given context.
        This function checks if the LLM has used a non-answer token or if the answer is similar to a list of predefined non-answers.
        Args:
            answers (list[str]): the answers from the LLM that will be checked
            non_answer_token (str): the non-answer token the LLM used. Defaults to NON_ANSWER_TOKEN.
            non_answer_examples (list[str]): a list of predefined non-answers. Defaults to NON_ANSWER_EXAMPLES.
            threshold (float, optional): . Defaults to 0.1, which is rather strict.

        Returns:
            list[bool]: a list of booleans indicating if the answer is a non-answer
        """
        assert threshold >= 0 and threshold <= 1
        has_not_found_token_exact = [
            self.non_answer_token.lower() in answer.lower() for answer in answers
        ]

        answer_embeds = self.embedding_model.encode(answers, normalize_embeddings=True)
        scores = util.dot_score(self.non_answers_embedded, answer_embeds)

        # return highest score for each answer
        max_scores = scores.max(axis=0).values.tolist()

        is_non_answer = []
        for has_not_found_token, max_score in zip(
            has_not_found_token_exact, max_scores
        ):
            if has_not_found_token:
                is_non_answer.append(True)
            elif max_score >= threshold:
                is_non_answer.append(True)
            else:
                is_non_answer.append(False)

        return is_non_answer


if __name__ == "__main__":
    question = "What is the use case of the app?"
    contexts = [
        "AI-Powered Presentation Generator which allows you to create presentations in 1 click. Slideforge is an AI-powered presentation generator that simplifies the process of creating impactful presentations. With just one click, Slideforge empowers users to transform their ideas into polished presentations effortlessly. Whether you provide a short prompt or a more detailed one (up to 400 characters), Slideforge swiftly generates a fully-fledged .pptx presentation. In a matter of 15-30 seconds, you'll have a slideshow with informative content, a logical structure, and beautiful images relevant to each slide. Experience the convenience of Slideforge, save valuable time, and enjoy the seamless creation of lovely presentations.",
        "I don't like apps that force me to subscribe to anything. It's so toxic!",
        "The product's price is way too high and it's very heavy",
    ]
    qa = QAProcessor()
    answers = qa.ask_question_to_texts(question, contexts)
    print(answers)

    answers = [
        "<NOT FOUND>",
        "The text does not give an answer to the question.",
        "The question can not be answered from the given context.",
        "The question cannot be answered from the given text.",
        "The context does not discuss any of that, so the answer is <NOT FOUND>.",
        "The context does not discuss any specific software problem.",
        "The software problem discussed in the given context is not clear.",
        "The software problem being discussed in the context is not mentioned.",
        "<not found>",
        "The software problem discussed in the given context is not explicitly mentioned. Therefore, the answer to the question is '<NOT FOUND>'.",
        "The software problem discussed in the given context is the lack of a power saver feature in desktop machines. The author suggests that it would be beneficial to have a power saver feature built into desktop machines to reduce power consumption when the machine is idle for a certain amount of time. This feature is already standard in portable machines, but not in desktop machines. The author mentions that defining what constitutes inactivity might be a tricky part of implementing this feature.",
        "You should use Slideforge because it is an AI-powered presentation generator that simplifies the process of creating impactful presentations. With just one click, Slideforge transforms your ideas into polished presentations effortlessly. It generates fully-fledged presentations with informative content, a logical structure, and beautiful images within seconds. By using Slideforge, you can save valuable time and enjoy the convenience of seamless presentation creation.",
        "The software problem discussed in the context is the inability to not find a morphing program called 'dmorph' and the limitation of another program called 'morpho' to only grayscale images.",
    ]

    # print("start")
    #
    # is_non_answer = qa.check_non_answers(answers=answers)

    # for answer, is_non_answer in zip(answers, is_non_answer):
    #    print(f"{answer} is non-answer: {is_non_answer}")
