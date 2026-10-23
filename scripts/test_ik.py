import unittest
import os
import sys
import sqlite3
import json

# Ensure parent directory and scripts directory are in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import server
from ik_onboarding_engine import validate_candidate_kep, generate_job_offer_document

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

    def test_table_schema_has_new_columns(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(applications)")
        columns = [row["name"] for row in cur.fetchall()]
        self.assertIn("kep_address", columns, "kep_address kolonu bulunmalıdır.")
        self.assertIn("cv_base64", columns, "cv_base64 kolonu bulunmalıdır.")
        self.assertIn("offer_salary", columns, "offer_salary kolonu bulunmalıdır.")
        self.assertIn("offer_start_date", columns, "offer_start_date kolonu bulunmalıdır.")
        self.assertIn("offer_letter_text", columns, "offer_letter_text kolonu bulunmalıdır.")

    def test_application_insert_and_retrieve_with_cv_and_kep(self):
        cur = self.conn.cursor()
        dummy_cv_base64 = "data:application/pdf;base64,JVBERi0xLjQKJUZha2VQREZDZ=="
        cur.execute("""
            INSERT INTO applications (
                tracking_code, position, full_name, id_number, phone, email,
                city, military_status, education_level, school_department,
                experience_years, salary_expectation, linkedin_url, cv_file_name,
                cover_letter, kep_address, cv_base64, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BASVURU-TEST-001",
            "Yazılım Geliştirici (Fullstack / Backend)",
            "Ahmet Yılmaz",
            "12345678901",
            "05551234567",
            "ahmet@example.com",
            "İstanbul",
            "Muaf / Yapıldı",
            "Lisans",
            "Bilgisayar Mühendisliği",
            "3 - 5 Yıl",
            "60.000 TL",
            "https://linkedin.com/in/ahmetyilmaz",
            "ahmet_yilmaz_cv.pdf",
            "Fullstack geliştirici deneyimim bulunmaktadır.",
            "ahmet.yilmaz@hs01.kep.tr",
            dummy_cv_base64,
            "Degerlendiriliyor",
            "2026-09-20T12:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM applications WHERE tracking_code = 'BASVURU-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["full_name"], "Ahmet Yılmaz")
        self.assertEqual(record["position"], "Yazılım Geliştirici (Fullstack / Backend)")
        self.assertEqual(record["status"], "Degerlendiriliyor")
        self.assertEqual(record["kep_address"], "ahmet.yilmaz@hs01.kep.tr")
        self.assertEqual(record["cv_base64"], dummy_cv_base64)

    def test_kep_validator_valid_and_invalid(self):
        # Valid cases
        v1 = validate_candidate_kep("ahmet.yilmaz@hs01.kep.tr")
        self.assertTrue(v1["valid"])
        self.assertEqual(v1["provider"], "hs01.kep.tr")

        v2 = validate_candidate_kep("mehmet.oz@turkkep.hs03.kep.tr")
        self.assertTrue(v2["valid"])

        # Invalid cases
        inv1 = validate_candidate_kep("mehmet@gmail.com")
        self.assertFalse(inv1["valid"])

        inv2 = validate_candidate_kep("gecersiz.adres")
        self.assertFalse(inv2["valid"])

        inv3 = validate_candidate_kep("")
        self.assertFalse(inv3["valid"])

    def test_generate_job_offer_document(self):
        candidate = {
            "tracking_code": "BASVURU-TEST-OFFER-1",
            "full_name": "Zeynep Kaya",
            "id_number": "98765432101",
            "position": "İnsan Kaynakları Uzmanı",
            "kep_address": "zeynep.kaya@hs01.kep.tr"
        }
        offer_data = {
            "salary": "55.000 TL Net",
            "start_date": "2026-11-01",
            "company_name": "Kurumsal Teknoloji A.Ş.",
            "company_kep": "ik@kurumsalteknoloji.kep.tr",
            "probation_period": "2 Ay"
        }

        doc = generate_job_offer_document(candidate, offer_data)
        self.assertIn("document_text", doc)
        self.assertIn("4857", doc["document_text"])
        self.assertIn("5070", doc["document_text"])
        self.assertIn("Zeynep Kaya", doc["document_text"])
        self.assertIn("55.000 TL Net", doc["document_text"])
        self.assertIn("zeynep.kaya@hs01.kep.tr", doc["document_text"])
        self.assertIn("ik@kurumsalteknoloji.kep.tr", doc["document_text"])

    def test_job_offer_creation_and_status_flow(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO applications (tracking_code, full_name, position, status)
            VALUES (?, ?, ?, ?)
        """, ("BASVURU-TEST-FLOW", "Mehmet Demir", "Muhasebe ve Finans Uzmanı", "Degerlendiriliyor"))
        self.conn.commit()

        # Update to Teklif Yapildi with salary and start date
        cur.execute("""
            UPDATE applications
            SET status = ?, offer_salary = ?, offer_start_date = ?, offer_letter_text = ?
            WHERE tracking_code = ?
        """, ("Teklif Yapildi", "52.000 TL", "2026-11-15", "Resmi Teklif Mektubu İçeriği", "BASVURU-TEST-FLOW"))
        self.conn.commit()

        cur.execute("SELECT status, offer_salary, offer_start_date, offer_letter_text FROM applications WHERE tracking_code = 'BASVURU-TEST-FLOW'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Teklif Yapildi")
        self.assertEqual(row["offer_salary"], "52.000 TL")
        self.assertEqual(row["offer_start_date"], "2026-11-15")
        self.assertIn("Resmi Teklif Mektubu", row["offer_letter_text"])

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "server.py")), "server.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "ik_onboarding_engine.py")), "ik_onboarding_engine.py bulunamadı")

if __name__ == "__main__":
    unittest.main()
