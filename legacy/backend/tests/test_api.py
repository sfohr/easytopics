import unittest
from io import BytesIO
from flask_testing import TestCase
from db import TextDB
from api import create_app


class FlaskTestCase(TestCase):
    def create_app(self):
        # Required by flask_testing
        app = create_app({"TESTING": True, "DATABASE": "tests/testing.sqlite3"})
        return app

    def setUp(self):
        with self.app.app_context():
            self.db = TextDB(self.app.config["DATABASE"])

    def tearDown(self):
        self.db.remove_all_documents()
        self.db.close_connection()

    def test_upload_csv(self):
        # Prepare a sample CSV data for testing
        tester = self.app.test_client(self)
        data = {
            "file": (
                BytesIO(b"id,text\n1,Test data\n2,Another test data"),
                "test.csv",
            )
        }

        response = tester.post(
            "/documents", content_type="multipart/form-data", data=data
        )

        # Assert response
        self.assert200(response)
        self.assertEqual(response.json["message"], "file uploaded successfully")
        self.assertEqual(len(self.db.get_documents()), 2)  # two rows inserted
        self.assertEqual(
            len(self.db.get_documents()[0]), 3
        )  # three columns in the table

    def test_upload_csv_without_file(self):
        tester = self.app.test_client(self)
        response = tester.post("/documents", content_type="multipart/form-data")
        self.assert400(response)
        self.assertEqual(response.json["error"], "No file part")

    def test_upload_csv_non_csv_file(self):
        tester = self.app.test_client(self)
        data = {"file": (BytesIO(b"This is not a CSV content"), "test.txt")}
        response = tester.post(
            "/documents", content_type="multipart/form-data", data=data
        )
        self.assert400(response)
        # self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Invalid file type")

    def test_get_documents(self):
        tester = self.app.test_client(self)
        data = {
            "file": (
                BytesIO(b"id,text\n1,Test Document\n2,Test Document 2"),
                "test.csv",
            )
        }

        _ = tester.post("/documents", content_type="multipart/form-data", data=data)
        response = tester.get("/documents", content_type="application/json")
        self.assert200(response)
        self.assertEqual(
            response.json,
            [
                {"id": 1, "text": "Test Document", "topic_id": None},
                {"id": 2, "text": "Test Document 2", "topic_id": None},
            ],
        )

    def test_get_document(self):
        tester = self.app.test_client(self)
        data = {
            "file": (
                BytesIO(b"id,text\n1,Test Document\n2,Test Document 2"),
                "test.csv",
            )
        }
        _ = tester.post("/documents", content_type="multipart/form-data", data=data)
        response = tester.get("/documents/1", content_type="application/json")
        self.assert200(response)
        self.assertEqual(response.json, [1, "Test Document", None])

    def test_add_topic_to_document(self):
        doc_id = 1
        topic_id = 1
        tester = self.app.test_client(self)
        data = {
            "file": (
                BytesIO(b"id,text\n1,Test Document\n2,Test Document 2"),
                "test.csv",
            )
        }
        _ = tester.post("/documents", content_type="multipart/form-data", data=data)
        response = tester.post(
            f"/documents/{doc_id}/{topic_id}", content_type="application/json"
        )
        self.assert200(response)
        self.assertEqual(self.db.get_document(doc_id), (1, "Test Document", 1))


if __name__ == "__main__":
    unittest.main()
