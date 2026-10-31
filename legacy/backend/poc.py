from db import TextDB
from qa import QAProcessor
from topicmodel import TopicModel
import pandas as pd

DEMO_FILE = "./20newsgroup_data_comp_20perCl.csv"
DEMO_DB = "./demo_20newsgroup_software_20perCl.sqlite3"
EXEMPLARY_OUTPUT = "./docs_answers_lbls.csv"
QUESTION = "What software problem is discussed?"

if __name__ == "__main__":
    db = TextDB(DEMO_DB)
    
    # read documents from file
    print(f"Reading demo file {DEMO_FILE}...")
    df = pd.read_csv(DEMO_FILE, sep=";")

    documents = df["text"].tolist()
    
    # insert documents into database
    if len(db.get_documents()) == 0:
        db.insert_documents(documents)
    else:
        print("Database already contains documents. Skipping insertion.")
    
    del documents

    if len(db.get_questions()) == 0:
        question_id = db.insert_question(QUESTION)
    else:
        print("Database already contains questions. Skipping insertion.")
        question_id = db.get_questions()[0][0]

    qa = QAProcessor()

    documents = db.get_documents()

    print(f"Found {len(documents)} documents in database.")

    if len(db.get_answers()) == 0:
        print("Asking question to each document...")
        for id_doc in documents:
            doc_id, doc = id_doc
            answer = qa.ask_question_to_txt(QUESTION, doc, debug=False)
            db.insert_answer(doc_id, question_id, answer)
    else:
        print("Database already contains answers. Skipping question answering.")

    # get answers from database
    answers = db.get_answers()
    answer_list = [answer for _, _, _, answer, _ in answers if "not found" not in answer.lower()]
    doc_ids = [doc_id for _, doc_id, _, answer, _ in answers if "not found" not in answer.lower()]

    print(f"Found {len(answer_list)} valid answers.")

    print("Starting topic model...")
    tm = TopicModel(answer_list, min_cluster=3, max_cluster=15, max_evals=20, seed=42423)
    best_params = tm.optim()

    lbls = tm.get_labels().tolist()

    for doc_id, lbl in zip(doc_ids, lbls):
        db.insert_topic_for_answer(doc_id, lbl)

    print(f"Dumping output to file {EXEMPLARY_OUTPUT}...")
    docs_answers_lbls = db.get_docs_with_answers_and_topic_ids()
    docs_answers_lbls = pd.DataFrame(docs_answers_lbls, columns=["doc_id", "doc", "answer", "topic_id"])
    docs_answers_lbls.to_csv(EXEMPLARY_OUTPUT, sep=";")