import sqlite3


class TextDB:
    def __init__(self, db_name: str = "texts.sqlite3") -> None:
        """Initializes the TextDB class

        Initializes the database and creates the tables if they do not exist.

        Args:
            db_name: the name of the database

        Returns:
            None
        """
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_tables()

    def __del__(self) -> None:
        """Closes the connection to the database when the object is deleted"""
        self.close_connection()

    def close_connection(self) -> None:
        """Closes the connection to the database"""
        self.conn.close()

    def init_tables(self) -> None:
        """
        Initialize the tables in the database.

        Creates tables Documents, Questions, Answers, Topics if they do not exist.

        """
        with self.conn as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS Topics (
              id INTEGER PRIMARY KEY,
              external_id INT NOT NULL,
              topic_representation TEXT NOT NULL
            )"""
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS Documents (
              id INTEGER PRIMARY KEY,
              doc TEXT NOT NULL,
              topic_id INTEGER,
              FOREIGN KEY (topic_id) REFERENCES Topics(id)
            )"""
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS Questions (
              id INTEGER PRIMARY KEY,
              question TEXT NOT NULL
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS Answers (
              id INTEGER PRIMARY KEY,
              doc_id INTEGER NOT NULL,
              question_id INTEGER NOT NULL,
              answer TEXT NOT NULL,
              CONSTRAINT fk_questions
                FOREIGN KEY (question_id)
                REFERENCES Questions(id) 
                ON DELETE CASCADE,
              CONSTRAINT fk_documents
                FOREIGN KEY (doc_id) 
                REFERENCES Documents(id) 
                ON DELETE CASCADE
            )
            """
            )

    def insert_document(self, doc: str) -> int:
        """Inserts a single document into the database

        Args:
          doc: the document to insert

        Returns:
          the id of the inserted document
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Documents (doc) VALUES (?)", (doc,))
            return cursor.lastrowid

    def remove_all_documents(self) -> None:
        """Removes all documents from the database

        Args:
          None

        Returns:
          None
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Documents")

    def insert_topic_for_document(self, doc_id: int, topic_id: int) -> None:
        """Inserts a topic for a document

        Args:
          doc_id: the id of the document
          topic_id: the id of the topic

        Returns:
          None
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Documents SET topic_id = ? WHERE id = ?", (topic_id, doc_id)
            )

    def insert_documents(self, docs: list[str]):
        """Inserts a list of documents into the database

        Args:
          docs: the documents to insert

        #Returns:
        #  the ids of the inserted documents
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO Documents (doc) VALUES (?)", [(doc,) for doc in docs]
            )

    def insert_topic(self, external_id: int, topic_representation: str) -> int:
        """Inserts a topic into the database

        Args:
          external_id: the external id of the topic
          topic_representation: the topic representation

        Returns:
          the id of the inserted topic
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Topics (external_id, topic_representation) VALUES (?, ?)",
                (external_id, topic_representation),
            )
            return cursor.lastrowid

    def insert_topics(self, topics: list[tuple[int, str]]):
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO Topics (external_id, topic_representation) VALUES (?, ?)",
                topics,
            )

    def insert_question(self, question: str) -> int:
        """Inserts a question into the database

        Args:
          question: the question to insert

        Returns:
          the id of the inserted question
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Questions (question) VALUES (?)", (question,))
            return cursor.lastrowid

    def remove_question(self, question_id: int) -> None:
        """Removes a question from the database

        Args:
          question_id: the id of the question to remove

        Returns:
          None
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Questions WHERE id = ?", (question_id,))

    def insert_answer(self, doc_id: int, question_id: int, answer: str) -> int:
        """Inserts a single answer into the database

        Args:
          doc_id: the id of the document
          question_id: the id of the question
          answer: the answer to insert

        Returns:
          the id of the inserted answer
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Answers (doc_id, question_id, answer) VALUES (?, ?, ?)",
                (doc_id, question_id, answer),
            )
            return cursor.lastrowid

    def remove_answer(self, answer_id: int) -> None:
        """Removes an answer from the database

        Args:
          answer_id: the id of the answer to remove

        Returns:
          None
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Answers WHERE id = ?", (answer_id,))

    def get_documents(self) -> list[tuple[int, str, int]]:
        """Returns all docs from Documents as a list

        Args:
          None

        Returns:
          a list of documents
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT * FROM Documents")
            raw = cursor.fetchall()
            keys = ["id", "text", "topic_id"]
            return [dict(zip(keys, row)) for row in raw]

    def get_document(self, doc_id: int) -> dict:
        """Returns a document from Documents as a dict

        Args:
            doc_id: the id of the document

        Returns:
            dict with keys "id", "text", "topic_id" or None if not found
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT * FROM Documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            keys = ["id", "text", "topic_id"]
            return dict(zip(keys, row))

    def get_documents_without_answer(self, question_id: int) -> list[tuple[int, str]]:
        """Returns all docs from Documents as a list

        Args:
          question_id (int): the id of the question

        Returns:
          a list of documents
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute(
                """
                SELECT d.id, d.doc
                FROM Documents d
                LEFT JOIN Answers a ON d.id = a.doc_id AND a.question_id = ?
                WHERE a.doc_id IS NULL
            """,
                (question_id,),
            )
            raw = cursor.fetchall()
            keys = ["id", "text"]
            return [dict(zip(keys, row)) for row in raw]

    def get_questions(self) -> list[str]:
        """Returns all questions from Questions as a list

        Args:
          None

        Returns:
          a list of questions
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT * FROM Questions")
            raw = cursor.fetchall()
            keys = ["id", "question"]
            return [dict(zip(keys, row)) for row in raw]

    def get_answers(self) -> list[str]:
        """Returns all answers from Answers as a list

        Args:
          None

        Returns:
          a list of answers
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute(
                """
                SELECT d.doc, a.answer, a.id, q.id
                FROM Answers a
                LEFT JOIN Documents d ON a.doc_id = d.id
                LEFT JOIN Questions q ON a.question_id = q.id
            """
            )
            raw = cursor.fetchall()
            keys = [
                "doc",
                "answer",
                "id",
                "question",
            ]
            return [dict(zip(keys, row)) for row in raw]

    def get_topics(self) -> list[str]:
        """Returns all topics from Topics as a list

        Args:
          None

        Returns:
          a list of topics
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT * FROM Topics")
            return cursor.fetchall()

    def get_answers_by_doc(self, doc_id: int) -> list[tuple]:
        """Returns all answers for a given document

        Args:
            doc_id: the id of the document

        Returns:
            a list of answers as tuples (id, doc_id, question_id, answer, topic_id)
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT * FROM Answers WHERE doc_id = ?", (doc_id,))
            return cursor.fetchall()

    def get_docs_with_answers(self) -> list[tuple]:
        """Returns all documents with answers

        Also returns documents without answers.

        Args:
            None

        Returns:
            a list of documents with answers as tuples (doc_id, doc, answer)
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute(
                """
                SELECT d.id, d.doc, a.answer
                FROM Documents d
                LEFT JOIN Answers a ON d.id = a.doc_id
            """
            )
            return cursor.fetchall()

    def get_docs_with_answers_and_topic_ids(self) -> list[tuple]:
        """Returns all documents with answers and topics

        Args:
            None

        Returns:
            a list of documents with answers and topics as tuples (doc_id, doc, answer, topic_id)
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor = cursor.execute(
                """
                SELECT d.id, d.doc, a.answer, d.topic_id
                FROM Documents d
                LEFT JOIN Answers a ON d.id = a.doc_id
            """
            )
            return cursor.fetchall()
