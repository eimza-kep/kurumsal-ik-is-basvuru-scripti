# -*- coding: utf-8 -*-
"""
server.py
---------
Kurumsal İK İşe Alım Portalı - Bağımsız Python SQLite Sunucusu.
- Aday iş ve staj başvuruları yönetimi
- PDF CV / Özgeçmiş önizleme ve indirme desteği
- KEP ve E-İmza uyumlu resmi iş teklif mektubu motoru
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse, parse_qs

# Windows console UTF-8 desteği
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.ik_onboarding_engine import (
    validate_candidate_kep,
    generate_job_offer_document
)

PORT = int(os.environ.get("PORT", 8084))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ik_basvurular.db"))

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            position TEXT,
            full_name TEXT,
            id_number TEXT,
            phone TEXT,
            email TEXT,
            city TEXT,
            military_status TEXT,
            education_level TEXT,
            school_department TEXT,
            experience_years TEXT,
            salary_expectation TEXT,
            linkedin_url TEXT,
            kep_address TEXT DEFAULT '',
            cv_file_name TEXT,
            cv_base64 TEXT DEFAULT '',
            cover_letter TEXT,
            status TEXT DEFAULT 'Degerlendiriliyor',
            offer_salary TEXT DEFAULT '',
            offer_start_date TEXT DEFAULT '',
            offer_letter_text TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    # Dinamik kolon güncelleme
    cur.execute("PRAGMA table_info(applications)")
    cols = [r[1] for r in cur.fetchall()]
    if "kep_address" not in cols:
        cur.execute("ALTER TABLE applications ADD COLUMN kep_address TEXT DEFAULT ''")
    if "cv_base64" not in cols:
        cur.execute("ALTER TABLE applications ADD COLUMN cv_base64 TEXT DEFAULT ''")
    if "offer_salary" not in cols:
        cur.execute("ALTER TABLE applications ADD COLUMN offer_salary TEXT DEFAULT ''")
    if "offer_start_date" not in cols:
        cur.execute("ALTER TABLE applications ADD COLUMN offer_start_date TEXT DEFAULT ''")
    if "offer_letter_text" not in cols:
        cur.execute("ALTER TABLE applications ADD COLUMN offer_letter_text TEXT DEFAULT ''")
    conn.commit()
    conn.close()

class IKHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kurumsal-ik-is-basvuru-scripti", "port": PORT})
        elif path == "/api/basvurular":
            self.handle_get_basvurular()
        elif path == "/api/istatistikler":
            self.handle_get_stats()
        elif path == "/api/teklif-goruntule":
            self.handle_get_offer(qs)
        elif path == "/api/validate-kep":
            kep = qs.get("kep", [""])[0]
            self.send_json(validate_candidate_kep(kep))
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/basvuru-yap":
            self.handle_create_basvuru()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        elif path == "/api/teklif-olustur":
            self.handle_create_offer()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_create_basvuru(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"BASVURU-2026-{random.randint(1000, 9999)}"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO applications (
                    tracking_code, position, full_name, id_number, phone, email,
                    city, military_status, education_level, school_department,
                    experience_years, salary_expectation, linkedin_url, kep_address,
                    cv_file_name, cv_base64, cover_letter, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_code,
                data.get("position", ""),
                data.get("full_name", ""),
                data.get("id_number", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("city", ""),
                data.get("military_status", ""),
                data.get("education_level", ""),
                data.get("school_department", ""),
                data.get("experience_years", ""),
                data.get("salary_expectation", ""),
                data.get("linkedin_url", ""),
                data.get("kep_address", ""),
                data.get("cv_file_name", ""),
                data.get("cv_base64", ""),
                data.get("cover_letter", ""),
                data.get("status", "Degerlendiriliyor"),
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "tracking_code": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_basvurular(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM applications ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self.send_json(rows)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("UPDATE applications SET status = ? WHERE tracking_code = ?", (new_status, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code, "new_status": new_status})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_create_offer(self):
        """Adaya resmi KEP iş teklifi oluşturur ve durumu günceller"""
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM applications WHERE tracking_code = ?", (tracking_code,))
            candidate = cur.fetchone()

            if not candidate:
                conn.close()
                self.send_json({"status": "error", "message": "Aday bulunamadı."}, status=404)
                return

            candidate_dict = dict(candidate)
            offer_result = generate_job_offer_document(candidate_dict, data)

            cur.execute("""
                UPDATE applications
                SET status = 'Teklif Yapildi',
                    offer_salary = ?,
                    offer_start_date = ?,
                    offer_letter_text = ?,
                    kep_address = ?
                WHERE tracking_code = ?
            """, (
                data.get("salary", candidate_dict.get("salary_expectation", "")),
                data.get("start_date", ""),
                offer_result["offer_text"],
                offer_result["candidate_kep"],
                tracking_code
            ))
            conn.commit()
            conn.close()

            self.send_json({
                "status": "success",
                "tracking_code": tracking_code,
                "offer_document": offer_result
            })
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_offer(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        if not tracking_code:
            self.send_json({"status": "error", "message": "Takip kodu girilmelidir."}, status=400)
            return

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT tracking_code, full_name, position, offer_salary, offer_start_date, offer_letter_text, kep_address FROM applications WHERE tracking_code = ?", (tracking_code,))
        row = cur.fetchone()
        conn.close()

        if not row:
            self.send_json({"status": "error", "message": "Teklif bulunamadı."}, status=404)
            return

        self.send_json({"status": "success", "data": dict(row)})

    def handle_get_stats(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM applications")
            total = cur.fetchone()[0]

            cur.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
            by_status = dict(cur.fetchall())

            cur.execute("SELECT position, COUNT(*) FROM applications GROUP BY position")
            by_position = dict(cur.fetchall())
            conn.close()

            self.send_json({
                "total": total,
                "by_status": by_status,
                "by_position": by_position
            })
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 Kurumsal IK Basvuru Portali Baslatildi: http://localhost:{port}")
    print(f"📊 Yonetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), IKHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatildi.")
