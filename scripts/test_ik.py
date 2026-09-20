import unittest
import os
import sys
import sqlite3
import json

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class TestIKApplicationSystem(unittest.TestCase):
    def setUp(self):
        server.init_db()
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("DELETE FROM applications WHERE tracking_code LIKE 'BASVURU-TEST%'")
        self.conn.commit()

    def tearDown(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM applications WHERE tracking_code LIKE 'BASVURU-TEST%'")
        self.conn.commit()
        self.conn.close()

    def test_database_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "applications tablosu oluşturulmuş olmalıdır.")

    def test_application_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO applications (
                tracking_code, position, full_name, id_number, phone, email,
                city, military_status, education_level, school_department,
                experience_years, salary_expectation, linkedin_url, cv_file_name,
                cover_letter, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BASVURU-TEST-001",
            "Yazılım Geliştirici (Fullstack / Backend)",
            "Test Aday",
            "12345678901",
            "05551234567",
            "test@example.com",
            "İstanbul",
            "Muaf / Yapıldı",
            "Lisans",
            "Bilgisayar Mühendisliği",
            "3 - 5 Yıl",
            "60.000 TL",
            "https://linkedin.com/in/test",
            "test_cv.pdf",
            "Test ön yazı metni",
            "Degerlendiriliyor",
            "2026-09-20T12:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM applications WHERE tracking_code = 'BASVURU-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["full_name"], "Test Aday")
        self.assertEqual(record["position"], "Yazılım Geliştirici (Fullstack / Backend)")
        self.assertEqual(record["status"], "Degerlendiriliyor")

    def test_status_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO applications (tracking_code, full_name, status)
            VALUES (?, ?, ?)
        """, ("BASVURU-TEST-002", "Mülakat Adayı", "Degerlendiriliyor"))
        self.conn.commit()

        cur.execute("UPDATE applications SET status = ? WHERE tracking_code = ?", ("Mulakata Cagrildi", "BASVURU-TEST-002"))
        self.conn.commit()

        cur.execute("SELECT status FROM applications WHERE tracking_code = 'BASVURU-TEST-002'")
        updated_status = cur.fetchone()[0]
        self.assertEqual(updated_status, "Mulakata Cagrildi")

    def test_html_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")

if __name__ == "__main__":
    unittest.main()
