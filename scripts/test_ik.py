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
from ik_onboarding_engine import (
    validate_candidate_kep,
    generate_job_offer_document,
    generate_job_offer_html,
    calculate_interview_score,
    calculate_pipeline_analytics,
    generate_pipeline_report_html,
    generate_ik_csv_export
)

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
        self.assertIn("interview_score", columns, "interview_score kolonu bulunmalıdır.")
        self.assertIn("interview_rating", columns, "interview_rating kolonu bulunmalıdır.")
        self.assertIn("interview_notes", columns, "interview_notes kolonu bulunmalıdır.")

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

    def test_job_offer_html_generation(self):
        candidate = {
            "tracking_code": "BASVURU-2026-TEST-HTML",
            "full_name": "Emre Can",
            "position": "Kıdemli Backend Geliştirici",
            "id_number": "12345678901",
            "phone": "05321112233",
            "email": "emre@test.com",
            "kep_address": "emre.can@hs01.kep.tr",
            "salary_expectation": "85.000 TL Net"
        }
        offer_data = {
            "salary": "90.000 TL Net",
            "start_date": "01.12.2026",
            "benefits": "Yol, Yemek, Özel Sağlık Sigortası, Yıllık Prim"
        }
        html = generate_job_offer_html(candidate, offer_data)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("BASVURU-2026-TEST-HTML", html)
        self.assertIn("Emre Can", html)
        self.assertIn("Kıdemli Backend Geliştirici", html)
        self.assertIn("90.000 TL Net", html)
        self.assertIn("emre.can@hs01.kep.tr", html)
        self.assertIn("4857 Sayılı İş Kanunu", html)
        self.assertIn("@media print", html)

    def test_calculate_interview_score(self):
        scores = {
            "technical_score": 4.5,
            "communication_score": 4.0,
            "problem_solving_score": 5.0,
            "cultural_fit_score": 4.5,
            "interviewer_notes": "Teknik mimari ve ekip liderliği kabiliyeti yüksek."
        }
        res = calculate_interview_score(scores)
        self.assertGreaterEqual(res["score_100"], 80)
        self.assertIn("Mükemmel", res["rating_label"])
        self.assertEqual(res["recommendation"], "Teklif Önerilir")
        self.assertEqual(res["interviewer_notes"], "Teknik mimari ve ekip liderliği kabiliyeti yüksek.")

    def test_calculate_pipeline_analytics(self):
        mock_apps = [
            {"status": "Degerlendiriliyor", "position": "Yazılım Geliştirici", "kep_address": "a@hs01.kep.tr", "cv_file_name": "cv1.pdf"},
            {"status": "Mulakata Cagrildi", "position": "Yazılım Geliştirici", "kep_address": "", "interview_score": 85.0},
            {"status": "Teklif Yapildi", "position": "Satış Temsilcisi", "kep_address": "b@hs02.kep.tr", "interview_score": 90.0},
            {"status": "Ise Alindi", "position": "Muhasebe", "kep_address": "c@hs03.kep.tr", "cv_file_name": "cv3.pdf", "interview_score": 88.0},
            {"status": "Reddedildi", "position": "Yazılım Geliştirici", "kep_address": "", "interview_score": 45.0}
        ]
        analytics = calculate_pipeline_analytics(mock_apps)
        self.assertEqual(analytics["total_applications"], 5)
        self.assertEqual(analytics["funnel"]["Ise Alindi"], 1)
        self.assertEqual(analytics["positions"]["Yazılım Geliştirici"], 3)
        self.assertEqual(analytics["interviewed_count"], 3)
        self.assertEqual(analytics["offered_count"], 2)
        self.assertEqual(analytics["hired_count"], 1)
        self.assertEqual(analytics["kep_usage_rate"], 60.0)
        self.assertGreater(analytics["average_interview_score"], 70.0)

    def test_generate_pipeline_report_html(self):
        analytics = {
            "report_date": "23.10.2026 21:30:00",
            "total_applications": 25,
            "funnel": {
                "Degerlendiriliyor": 10,
                "On Eleme Gecti": 5,
                "Mulakata Cagrildi": 4,
                "Teklif Yapildi": 3,
                "Ise Alindi": 2,
                "Reddedildi": 1
            },
            "positions": {"Yazılım": 15, "Satış": 7, "Muhasebe": 3},
            "interviewed_count": 9,
            "offered_count": 5,
            "hired_count": 2,
            "app_to_interview_rate": 36.0,
            "interview_to_offer_rate": 55.6,
            "offer_to_hire_rate": 40.0,
            "kep_usage_rate": 48.0
        }
        report = generate_pipeline_report_html(analytics, "Test Şirketi A.Ş.")
        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn("Test Şirketi A.Ş.", report)
        self.assertIn("İNSAN KAYNAKLARI DİREKTÖRLÜĞÜ", report)
        self.assertIn("25", report)
        self.assertIn("RECRUITMENT FUNNEL", report)

    def test_generate_ik_csv_export(self):
        apps = [
            {
                "tracking_code": "BASVURU-2026-901",
                "full_name": "Gökhan Arslan",
                "id_number": "12345678901",
                "phone": "05331112233",
                "email": "gokhan@test.com",
                "city": "İstanbul",
                "position": "DevOps Mühendisi",
                "experience_years": "5 Yıl",
                "education_level": "Lisans",
                "school_department": "Bilgisayar Mühendisliği",
                "salary_expectation": "95.000 TL",
                "offer_salary": "100.000 TL",
                "offer_start_date": "01.12.2026",
                "interview_score": 92.5,
                "interview_rating": "Mükemmel",
                "kep_address": "gokhan@hs01.kep.tr",
                "status": "Ise Alindi",
                "created_at": "2026-10-23T10:00:00Z"
            }
        ]
        csv_out = generate_ik_csv_export(apps)
        self.assertTrue(csv_out.startswith("\ufeff"), "Excel uyumlu UTF-8 BOM olmalıdır.")
        self.assertIn("BASVURU-2026-901", csv_out)
        self.assertIn("Gökhan Arslan", csv_out)
        self.assertIn("DevOps Mühendisi", csv_out)
        self.assertIn("92.5", csv_out)
        self.assertIn("gokhan@hs01.kep.tr", csv_out)

    def test_interview_evaluation_db_flow(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO applications (tracking_code, full_name, position, status)
            VALUES (?, ?, ?, ?)
        """, ("BASVURU-TEST-SCORE", "Derya Şen", "Ürün Yöneticisi", "Mulakata Cagrildi"))
        self.conn.commit()

        # Update interview score
        cur.execute("""
            UPDATE applications
            SET interview_score = ?, interview_rating = ?, interview_notes = ?, interviewer_name = ?
            WHERE tracking_code = ?
        """, (86.5, "Mükemmel (Doğrudan Teklif)", "Ürün vizyonu güçlü", "İK Müdürü", "BASVURU-TEST-SCORE"))
        self.conn.commit()

        cur.execute("SELECT interview_score, interview_rating, interview_notes, interviewer_name FROM applications WHERE tracking_code = 'BASVURU-TEST-SCORE'")
        row = cur.fetchone()
        self.assertEqual(row["interview_score"], 86.5)
        self.assertEqual(row["interview_rating"], "Mükemmel (Doğrudan Teklif)")
        self.assertEqual(row["interview_notes"], "Ürün vizyonu güçlü")
        self.assertEqual(row["interviewer_name"], "İK Müdürü")

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "server.py")), "server.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "ik_onboarding_engine.py")), "ik_onboarding_engine.py bulunamadı")

if __name__ == "__main__":
    unittest.main()
