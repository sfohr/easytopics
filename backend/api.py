from flask import Flask, request, jsonify
from db import TextDB
from topicmodel import TopicModel
from qa import QAProcessor
from sentence_transformers import SentenceTransformer
import pandas as pd
import os, random
from config import EMBEDDING_MODEL


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=os.path.join(app.instance_path, "demo.sqlite"))
    sentence_transformer = SentenceTransformer(EMBEDDING_MODEL)
    question_answer = QAProcessor(embedding_model=sentence_transformer)

    if test_config:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db = TextDB(app.config["DATABASE"])

    @app.route("/documents", methods=["POST"])
    def upload_csv():
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and file.filename.endswith(".csv"):
            docs = pd.read_csv(
                file, sep=",", usecols=["text"], dtype={"text": str}, encoding="utf-8"
            )["text"].to_list()

            db.insert_documents(docs)

            return jsonify({"message": "file uploaded successfully"}), 200

        return jsonify({"error": "Invalid file type"}), 400

    @app.route("/documents", methods=["GET"])
    def get_documents():
        documents = db.get_documents()
        if len(documents) == 0:
            return jsonify({"error": "No documents found"}), 404
        return jsonify(documents), 200

    @app.route("/documents/<int:doc_id>", methods=["GET"])
    def get_document(doc_id: int):
        document = db.get_document(doc_id)
        if document is None:
            return jsonify({"error": "Document not found"}), 404
        return jsonify(document), 200

    @app.route("/documents/<int:doc_id>/<int:topic_id>", methods=["POST"])
    def add_topic_to_document(doc_id: int, topic_id: int):
        document = db.get_document(doc_id)
        if document is None:
            return jsonify({"error": "Document not found"}), 404
        db.insert_topic_for_document(doc_id, topic_id)
        return jsonify({"message": "Topic added successfully"}), 200

    @app.route("/questions", methods=["POST"])
    def add_question():
        question = request.json["question"]
        rowid = db.insert_question(question)
        return jsonify({"message": "Question added successfully", "id": rowid}), 200

    @app.route("/questions", methods=["GET"])
    def get_questions():
        questions = db.get_questions()
        if len(questions) == 0:
            return jsonify({"error": "No questions found"}), 404
        return jsonify(questions), 200

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def remove_question(question_id: int):
        db.remove_question(question_id)
        return jsonify({"message": "Question removed successfully"}), 200

    @app.route("/ask_question", methods=["POST"])
    def ask_question():
        try_questions = request.json["tryout"]
        if try_questions == True:
            documents = db.get_documents()
            question = request.json["question"]
            k = request.json.get("k", 2)
             # randomly sample k documents (or all if k > len(documents))
            k = min(int(k), len(documents))
            documents = random.sample(documents, k=k)

            texts = [doc["text"] for doc in documents]
            answers = question_answer.ask_question_to_texts(question, texts=texts)
            for answer, doc in zip(answers, documents):
                doc["question"] = question
                doc["answer"] = answer

            # insert question into db
            question_id = db.insert_question(question)

            # insert answers into db
            for doc in documents:
                db.insert_answer(doc["id"], question_id, doc["answer"])

            return jsonify(documents), 200

        if try_questions == False:
            questions = db.get_questions()
            for question in questions:
                question_id = question["id"]
                question_text = question["question"]
                documents = db.get_documents_without_answer(question_id)
                texts = [doc["text"] for doc in documents]
                # get answers for each question
                answers = question_answer.ask_question_to_texts(
                    question_text, texts=texts
                )
                for answer, doc in zip(answers, documents):
                    doc["question"] = question_text
                    doc["answer"] = answer
                for doc in documents:
                    db.insert_answer(doc["id"], question_id, doc["answer"])
            return jsonify(documents), 200

    @app.route("/answers", methods=["GET"])
    def get_answers():
        answers = db.get_answers()
        if len(answers) == 0:
            return jsonify({"error": "No answers found"}), 404
        return jsonify(answers), 200

    @app.route("/topics", methods=["POST"])
    def add_topics():
        topics = request.json["topics"]
        rowid = db.insert_topics(topics)
        return jsonify({"message": "Topics added successfully"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
