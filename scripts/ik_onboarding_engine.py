# -*- coding: utf-8 -*-
"""
ik_onboarding_engine.py
-----------------------
Kurumsal İK İşe Alım, KEP Resmi Teklif Mektubu ve CV Önizleme Motoru.
4857 Sayılı İş Kanunu ve BTK KEP Standartları ile tam uyumlu:
- BTK KEP Doğrulayıcı
- Metin Formatında KEP İş Teklifi Mektubu
- A4 Formatında Resmi İş Teklifi ve İşe Başlama Protokolü (HTML / PDF)
- Mülakat Puanlama ve Yetkinlik Değerlendirme Kartı (Interview Scorecard)
- İK Yıllık İşe Alım Pipeline Analitiği & Faaliyet Raporu
- Excel Uyumlu UTF-8 BOM CSV Dışa Aktarımı
"""

import re
import datetime
from html import escape
from typing import Dict, List, Any, Optional

RECOGNIZED_KEP_PROVIDERS = [
    "hs01.kep.tr",
    "hs02.kep.tr",
    "hs03.kep.tr",
    "hs04.kep.tr",
    "hs05.kep.tr",
    "hs06.kep.tr",
    "hs07.kep.tr",
    "hs08.kep.tr",
    "hs09.kep.tr",
    "tnb.kep.tr",
    "turkkep.kep.tr",
    "e-tugra.kep.tr"
]

DEFAULT_COMPANY = {
    "company_name": "KURUMSAL BİLİŞİM VE VERİ TEKNOLOJİLERİ A.Ş.",
    "company_kep": "ik@hs01.kep.tr",
    "address": "Bilişim Vadisi, Teknoloji Blokları No:42/A Gebze / Kocaeli",
    "tax_id": "5810492810 / Kocaeli İhtisas V.D.",
    "hr_director": "Ayşe Yılmaz (İnsan Kaynakları Direktörü)",
    "phone": "0262 678 00 00",
    "email": "kariyer@kurumsal.com.tr"
}

def validate_candidate_kep(kep: Optional[str]) -> Dict[str, Any]:
    """
    Adayın KEP adresinin BTK standartlarına uygunluğunu doğrular.
    """
    if not kep or not isinstance(kep, str):
        return {"valid": False, "code": "EMPTY", "message": "KEP adresi boş."}

    kep = kep.strip().lower()
    kep_regex = r"^[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9_\.\-]+\.kep\.tr$"
    if not re.match(kep_regex, kep):
        return {
            "valid": False,
            "code": "INVALID_FORMAT",
            "message": "Geçersiz KEP formatı. Adres '.kep.tr' uzantılı olmalıdır."
        }

    domain_part = kep.split("@")[1]
    is_recognized = any(domain_part == rec or domain_part.endswith("." + rec) for rec in RECOGNIZED_KEP_PROVIDERS)

    return {
        "valid": True,
        "code": "OK",
        "kep_address": kep,
        "domain": domain_part,
        "provider": domain_part,
        "is_official": is_recognized,
        "message": f"Geçerli KEP adresi ({domain_part})."
    }

def generate_job_offer_document(candidate: Dict[str, Any], offer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    4857 Sayılı İş Kanunu uyarınca adaya KEP / E-İmza üzerinden iletilecek
    resmi iş teklifi ve işe başlama metnini üretir.
    """
    name = candidate.get("full_name", "Sayın Aday")
    position = candidate.get("position", "Belirtilmemiş Pozisyon")
    tc = candidate.get("id_number", "TCKN")
    kep = candidate.get("kep_address") or offer_data.get("candidate_kep", "Belirtilmedi")
    
    company_name = offer_data.get("company_name", DEFAULT_COMPANY["company_name"])
    company_kep = offer_data.get("company_kep", DEFAULT_COMPANY["company_kep"])
    salary = offer_data.get("salary", candidate.get("salary_expectation", "Piyasa Koşulları"))
    start_date = offer_data.get("start_date", datetime.date.today().strftime("%d.%m.%Y"))
    benefits = offer_data.get("benefits", "Yol, Yemek (Multinet), Özel Sağlık Sigortası, Yıllık Performans Primi")

    today_str = datetime.date.today().strftime("%d.%m.%Y")
    ref_code = f"TEKLIF-{candidate.get('tracking_code', 'IK-2026')}"

    offer_text = f"""
================================================================================
                      {company_name.upper()}
               RESMİ İŞ TEKLİFİ VE İŞE BAŞLAMA BEYANNAMESİ
================================================================================
Tarih          : {today_str}
Ref / KEP No   : {ref_code}
Gönderici KEP  : {company_kep}
Muhatap KEP    : {kep}

Sayın {name} (T.C. Kimlik No: {tc}),

Şirketimiz bünyesinde açık bulunan "{position}" pozisyonu için gerçekleştirilen
mülakat ve değerlendirme süreçleri neticesinde, yetkinliklerinizin pozisyon
ihtiyaçlarımızla tam uyum sağladığı memnuniyetle tespit edilmiştir.

Bu doğrultuda şirketimiz ailesine katılmanız amacıyla işbu resmi iş teklifini
tarafınıza sunmaktan onur duyarız.

İŞ VE ÇALIŞMA KOŞULLARI:
--------------------------------------------------------------------------------
1. Pozisyon Unvanı  : {position}
2. Görev Başlangıcı : {start_date}
3. Aylık Net Ücret  : {salary}
4. Sosyal Haklar    : {benefits}
5. Çalışma Esası    : 4857 Sayılı İş Kanunu Hükümleri Uyarınca Tam Zamanlı
6. Deneme Süresi    : 2 (İki) Ay

KABUL VE ONAY:
İşbu teklif mektubunun tarafınızca uygun bulunması halinde, 5070 Sayılı Elektronik
İmza Kanunu uyarınca güvenli e-imzanız ile imzalanarak şirketimiz KEP adresine
({company_kep}) iletilmesi veya basılı nüshanın ıslak imzalı olarak İnsan Kaynakları
Direktörlüğümüze teslimi rica olunur.

Saygılarımızla,
{company_name} İnsan Kaynakları Direktörlüğü
================================================================================
""".strip()

    return {
        "ref_code": ref_code,
        "candidate_name": name,
        "position": position,
        "salary": salary,
        "start_date": start_date,
        "candidate_kep": kep,
        "company_kep": company_kep,
        "offer_text": offer_text,
        "document_text": offer_text
    }

def generate_job_offer_html(candidate: Dict[str, Any], offer_data: Dict[str, Any], company_info: Optional[Dict[str, Any]] = None) -> str:
    """
    4857 Sayılı İş Kanunu ve 5070 Sayılı Elektronik İmza Kanunu uyumlu,
    A4 formatında resmi, yazdırılabilir ve PDF olarak kaydedilebilir
    'RESMİ İŞ TEKLİFİ VE İŞE BAŞLAMA PROTOKOLÜ' belgesi üretir.
    """
    comp = company_info or DEFAULT_COMPANY
    name = candidate.get("full_name", "Sayın Aday")
    position = candidate.get("position", "Belirtilmemiş Pozisyon")
    tc = candidate.get("id_number", "-")
    phone = candidate.get("phone", "-")
    email = candidate.get("email", "-")
    kep = candidate.get("kep_address") or offer_data.get("candidate_kep", "Belirtilmedi")

    salary = offer_data.get("salary") or candidate.get("salary_expectation", "Görüşülecektir")
    start_date = offer_data.get("start_date") or datetime.date.today().strftime("%d.%m.%Y")
    benefits = offer_data.get("benefits", "Yol, Yemek (Multinet Kartı), Kapsamlı Özel Sağlık Sigortası, Yıllık Performans Primi, Şirket Donanımı (MacBook Pro)")
    trial_period = offer_data.get("trial_period", "2 (İki) Ay - 4857 Sayılı İş Kanunu Madde 15")
    today_str = datetime.date.today().strftime("%d.%m.%Y")
    tracking_code = candidate.get("tracking_code", "IK-2026-0000")
    ref_code = f"TEKLIF-{tracking_code}"

    benefits_items = [b.strip() for b in benefits.split(",") if b.strip()]
    benefits_html = "".join([f"<li>✔ {escape(b)}</li>" for b in benefits_items]) or "<li>Standart Şirket Yan Hakları</li>"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Resmi İş Teklifi Mektubu - {escape(ref_code)}</title>
<style>
  * {{ box-sizing: border-box; font-family: 'Times New Roman', Times, serif; }}
  body {{ background: #f8fafc; padding: 24px 16px; color: #0f172a; margin: 0; line-height: 1.45; }}
  .toolbar {{ max-width: 820px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: white; padding: 12px 20px; border-radius: 8px; border: 1px solid #cbd5e1; font-family: sans-serif; }}
  .doc-container {{ max-width: 820px; margin: auto; background: white; border: 2px solid #0f172a; padding: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
  .header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 18px; }}
  .header h1 {{ margin: 0; font-size: 1.25rem; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; }}
  .header h2 {{ font-size: 1.05rem; margin: 4px 0; color: #0284c7; font-family: sans-serif; font-weight: 800; }}
  .header p {{ margin: 4px 0 0 0; font-size: 0.85rem; font-family: sans-serif; color: #475569; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; font-size: 0.9rem; font-family: sans-serif; }}
  .meta-box {{ border: 1px solid #cbd5e1; padding: 10px 12px; border-radius: 4px; background: #fafafa; line-height: 1.5; }}
  .offer-banner {{ padding: 10px; border-radius: 6px; font-family: sans-serif; font-weight: 800; text-align: center; font-size: 0.95rem; margin-bottom: 16px; background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }}
  .section-title {{ font-size: 0.95rem; font-weight: bold; margin: 14px 0 6px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; text-transform: uppercase; font-family: sans-serif; color: #0f172a; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 0.88rem; font-family: sans-serif; }}
  th, td {{ padding: 8px 10px; border: 1px solid #cbd5e1; }}
  th {{ background: #f1f5f9; text-align: left; }}
  ul {{ margin: 6px 0 12px 20px; padding: 0; font-size: 0.88rem; }}
  .legal-box {{ background: #f8fafc; border-left: 4px solid #0284c7; padding: 10px 14px; margin: 16px 0; font-size: 0.82rem; font-family: sans-serif; line-height: 1.5; color: #334155; }}
  .signatures {{ display: flex; justify-content: space-between; margin-top: 36px; padding-top: 20px; border-top: 1px dashed #cbd5e1; font-family: sans-serif; }}
  .sig-block {{ width: 45%; text-align: center; font-size: 0.88rem; }}
  @media print {{
    body {{ background: transparent; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .doc-container {{ border: none; padding: 0; box-shadow: none; max-width: 100%; }}
  }}
</style>
</head>
<body>

<div class="toolbar">
  <span style="font-weight: 700; font-size: 0.9rem;">📨 4857 Sayılı Kanun Uyumlu İş Teklifi Belgesi ({escape(ref_code)})</span>
  <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85rem;">🖨️ Yazdır / PDF Olarak Kaydet</button>
</div>

<div class="doc-container">
  <div class="header">
    <h1>{escape(comp['company_name'])}</h1>
    <h2>RESMİ İŞ TEKLİFİ VE İŞE BAŞLAMA PROTOKOLÜ</h2>
    <p>Belge Ref: <b>{escape(ref_code)}</b> | Tarih: <b>{today_str}</b> | Takip Kodu: <b>{escape(tracking_code)}</b></p>
  </div>

  <div class="meta-grid">
    <div class="meta-box">
      <b>İŞVEREN BİLGİLERİ:</b><br>
      <b>Şirket:</b> {escape(comp['company_name'])}<br>
      <b>Adres:</b> {escape(comp['address'])}<br>
      <b>Vergi / Mersis:</b> {escape(comp['tax_id'])}<br>
      <b>Gönderici KEP:</b> {escape(comp['company_kep'])}<br>
      <b>İletişim:</b> {escape(comp['phone'])}
    </div>
    <div class="meta-box">
      <b>ADAY (ÇALIŞAN ADAYI) BİLGİLERİ:</b><br>
      <b>Adı Soyadı:</b> {escape(name)}<br>
      <b>T.C. Kimlik No:</b> {escape(tc)}<br>
      <b>Telefon / E-Posta:</b> {escape(phone)} / {escape(email)}<br>
      <b>Aday KEP Adresi:</b> {escape(kep)}<br>
      <b>Teklif Edilen Pozisyon:</b> {escape(position)}
    </div>
  </div>

  <div class="offer-banner">
    TEBRİKLER! "{escape(position).upper()}" POZİSYONUNA KABUL EDİLDİNİZ
  </div>

  <div class="section-title">1. İŞ VE ÇALIŞMA KOŞULLARI</div>
  <table>
    <tbody>
      <tr>
        <th style="width:35%;">Teklif Edilen Pozisyon</th>
        <td><b>{escape(position)}</b></td>
      </tr>
      <tr>
        <th>Görev Başlangıç Tarihi</th>
        <td><b>{escape(start_date)}</b></td>
      </tr>
      <tr>
        <th>Aylık Net Ücret</th>
        <td><b style="color:#0284c7; font-size:1rem;">{escape(salary)}</b></td>
      </tr>
      <tr>
        <th>Çalışma Şekli &amp; Esası</th>
        <td>4857 Sayılı İş Kanunu Hükümleri Uyarınca Tam Zamanlı (Haftalık 45 Saat)</td>
      </tr>
      <tr>
        <th>Yasal Deneme Süresi</th>
        <td>{escape(trial_period)}</td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">2. SAĞLANAN YAN VE SOSYAL HAKLAR</div>
  <ul>
    {benefits_html}
  </ul>

  <div class="section-title">3. YASAL BİLDİRİM, E-İMZA VE KEP TEBELLÜĞ ESASLARI</div>
  <div class="legal-box">
    <b>⚖️ 5070 Sayılı Elektronik İmza Kanunu ve 4857 Sayılı İş Kanunu Hükümleri:</b><br>
    İşbu iş teklif mektubu, taraflar arasında iş sözleşmesinin esaslı unsurlarını belirlemekte olup bağlayıcıdır. Teklifi kabul etmeniz halinde; metni 5070 Sayılı Kanun'a uygun Nitelikli Elektronik Sertifikanız (E-İmza) ile imzalayarak şirketimizin <b>{escape(comp['company_kep'])}</b> KEP adresine iletebilir veya aşağıdaki kabul alanını ıslak imzalayarak en geç <b>7 (yedi) iş günü</b> içerisinde İnsan Kaynakları Direktörlüğümüze teslim edebilirsiniz.
  </div>

  <div class="signatures">
    <div class="sig-block">
      <b>ADAY / ÇALIŞAN</b><br>
      {escape(name)}<br>
      <small>Teklifi Kabul Eden</small><br>
      <div style="height:35px;"></div>
      Tarih &amp; Islak / E-İmza
    </div>
    <div class="sig-block">
      <b>İŞVEREN YETKİLİSİ</b><br>
      {escape(comp['hr_director'])}<br>
      <small>İnsan Kaynakları Direktörlüğü</small><br>
      <div style="height:35px;"></div>
      Şirket Kaşesi &amp; Yetkili İmza
    </div>
  </div>
</div>

</body>
</html>"""

def calculate_interview_score(scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adayın mülakat yetkinlik puanlarını ağırlıklandırarak genel skorunu hesaplar.
    Ağırlıklar:
    - Teknik Yetkinlik: %35
    - İletişim & İfade: %25
    - Problem Çözme & Analitik: %20
    - Şirket Kültürüne Uyum: %20
    """
    tech = max(1.0, min(5.0, float(scores.get("technical_score", 3.0))))
    comm = max(1.0, min(5.0, float(scores.get("communication_score", 3.0))))
    prob = max(1.0, min(5.0, float(scores.get("problem_solving_score", 3.0))))
    cult = max(1.0, min(5.0, float(scores.get("cultural_fit_score", 3.0))))

    weighted_5 = (tech * 0.35) + (comm * 0.25) + (prob * 0.20) + (cult * 0.20)
    score_100 = round((weighted_5 / 5.0) * 100, 1)

    if score_100 >= 85:
        rating_label = "Mükemmel (Doğrudan Teklif)"
    elif score_100 >= 70:
        rating_label = "Çok İyi (Öncelikli Aday)"
    elif score_100 >= 55:
        rating_label = "Yeterli (Yedek Aday)"
    else:
        rating_label = "Yetersiz (Olumsuz)"

    recommendation = scores.get("recommendation")
    if not recommendation:
        recommendation = "Teklif Önerilir" if score_100 >= 70 else ("Yedek Aday" if score_100 >= 55 else "Olumsuz")

    return {
        "technical_score": tech,
        "communication_score": comm,
        "problem_solving_score": prob,
        "cultural_fit_score": cult,
        "weighted_rating": round(weighted_5, 2),
        "score_100": score_100,
        "rating_label": rating_label,
        "recommendation": recommendation,
        "interviewer_notes": scores.get("interviewer_notes", ""),
        "evaluated_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    }

def calculate_pipeline_analytics(applications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    İK Direktörlüğü için işe alım funnel ve aday dönüşüm metriklerini hesaplar.
    """
    total = len(applications)
    funnel = {
        "Degerlendiriliyor": 0,
        "On Eleme Gecti": 0,
        "Mulakata Cagrildi": 0,
        "Teklif Yapildi": 0,
        "Ise Alindi": 0,
        "Reddedildi": 0
    }

    positions: Dict[str, int] = {}
    kep_count = 0
    cv_count = 0
    scores_list = []

    for app in applications:
        st = app.get("status", "Degerlendiriliyor")
        # normalize turkish characters if any
        norm_st = st.replace("ı", "i").replace("ğ", "g").replace("ş", "s").replace("ü", "u").replace("ö", "o").replace("ç", "c")
        matched = False
        for k in funnel.keys():
            if k.lower() in norm_st.lower() or norm_st.lower() in k.lower():
                funnel[k] += 1
                matched = True
                break
        if not matched:
            funnel["Degerlendiriliyor"] += 1

        pos = app.get("position", "Diğer")
        positions[pos] = positions.get(pos, 0) + 1

        if app.get("kep_address") and app.get("kep_address").strip():
            kep_count += 1
        if app.get("cv_base64") or app.get("cv_file_name"):
            cv_count += 1

        score = app.get("interview_score")
        if score is not None and score != "":
            try:
                scores_list.append(float(score))
            except Exception:
                pass

    interviewed = funnel["Mulakata Cagrildi"] + funnel["Teklif Yapildi"] + funnel["Ise Alindi"]
    offered = funnel["Teklif Yapildi"] + funnel["Ise Alindi"]
    hired = funnel["Ise Alindi"]

    app_to_interview_rate = round((interviewed / total * 100), 1) if total else 0.0
    interview_to_offer_rate = round((offered / interviewed * 100), 1) if interviewed else 0.0
    offer_to_hire_rate = round((hired / offered * 100), 1) if offered else 0.0

    kep_rate = round((kep_count / total * 100), 1) if total else 0.0
    cv_rate = round((cv_count / total * 100), 1) if total else 0.0
    avg_score = round(sum(scores_list) / len(scores_list), 1) if scores_list else 0.0

    return {
        "report_date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "total_applications": total,
        "funnel": funnel,
        "positions": positions,
        "interviewed_count": interviewed,
        "offered_count": offered,
        "hired_count": hired,
        "app_to_interview_rate": app_to_interview_rate,
        "interview_to_offer_rate": interview_to_offer_rate,
        "offer_to_hire_rate": offer_to_hire_rate,
        "kep_usage_rate": kep_rate,
        "cv_attachment_rate": cv_rate,
        "average_interview_score": avg_score
    }

def generate_pipeline_report_html(analytics: Dict[str, Any], company_name: str = DEFAULT_COMPANY["company_name"]) -> str:
    """
    A4 formatında yazdırılabilir İK Yıllık İşe Alım & Aday Pipeline Raporu üretir.
    """
    total = analytics.get("total_applications", 0)
    funnel = analytics.get("funnel", {})
    positions = analytics.get("positions", {})

    pos_rows = "".join([
        f"<tr><td style='padding:8px 12px; border:1px solid #cbd5e1;'>💼 {escape(pos)}</td><td style='padding:8px 12px; border:1px solid #cbd5e1; text-align:right; font-weight:bold;'>{cnt}</td><td style='padding:8px 12px; border:1px solid #cbd5e1; text-align:right;'>%{round(cnt/total*100, 1) if total else 0}</td></tr>"
        for pos, cnt in sorted(positions.items(), key=lambda x: x[1], reverse=True)
    ])

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Kurumsal İK İşe Alım &amp; Pipeline Faaliyet Raporu</title>
<style>
  * {{ box-sizing: border-box; font-family: 'Times New Roman', Times, serif; }}
  body {{ background: #f8fafc; padding: 24px 16px; color: #0f172a; margin: 0; }}
  .toolbar {{ max-width: 860px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: white; padding: 12px 20px; border-radius: 8px; border: 1px solid #cbd5e1; font-family: sans-serif; }}
  .doc-container {{ max-width: 860px; margin: auto; background: white; border: 2px solid #0f172a; padding: 36px; }}
  .header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 20px; font-family: sans-serif; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; font-family: sans-serif; }}
  .kpi-card {{ border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center; background: #fafafa; }}
  .kpi-val {{ font-size: 1.6rem; font-weight: 800; color: #0284c7; }}
  .kpi-lbl {{ font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-top: 4px; }}
  .section-title {{ font-size: 0.95rem; font-weight: bold; margin: 18px 0 8px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; text-transform: uppercase; font-family: sans-serif; color: #0f172a; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 0.88rem; font-family: sans-serif; }}
  th {{ background: #f1f5f9; padding: 10px 12px; border: 1px solid #cbd5e1; text-align: left; }}
  td {{ border: 1px solid #cbd5e1; }}
  @media print {{
    body {{ background: transparent; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .doc-container {{ border: none; padding: 0; box-shadow: none; max-width: 100%; }}
  }}
</style>
</head>
<body>

<div class="toolbar">
  <span style="font-weight: 700; font-size: 0.9rem;">📊 İK Yıllık Yetenek Kazanımı ve Aday Pipeline Raporu</span>
  <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85rem;">🖨️ Yazdır / PDF Kaydet</button>
</div>

<div class="doc-container">
  <div class="header">
    <h1 style="font-size:1.2rem; margin:0; font-weight:800;">{escape(company_name)}</h1>
    <h2 style="font-size:1.05rem; margin:4px 0; color:#0284c7;">İNSAN KAYNAKLARI DİREKTÖRLÜĞÜ İŞE ALIM VE YETENEK PİPELİNE FAALİYET RAPORU</h2>
    <p style="font-size:0.85rem; color:#64748b; margin:2px 0;">Rapor Tarihi: {analytics['report_date']} | Rapor Türü: Kurumsal İK İstatistiği</p>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-val">{total}</div>
      <div class="kpi-lbl">Toplam Aday Başvurusu</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val" style="color:#0284c7;">{analytics.get('interviewed_count', 0)}</div>
      <div class="kpi-lbl">Mülakata Alınan</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val" style="color:#16a34a;">{analytics.get('hired_count', 0)}</div>
      <div class="kpi-lbl">İşe Alınan Aday</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val" style="color:#7c3aed;">%{analytics.get('kep_usage_rate', 0)}</div>
      <div class="kpi-lbl">KEP / E-İmza Kullanımı</div>
    </div>
  </div>

  <div class="section-title">1. İŞE ALIM HUNİSİ (RECRUITMENT FUNNEL) DÖNÜŞÜM ORANLARI</div>
  <table>
    <thead>
      <tr>
        <th>Huni Aşaması</th>
        <th style="text-align:right;">Aday Sayısı</th>
        <th style="text-align:right;">Dönüşüm / Oran</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding:8px 12px;">📥 Yeni Başvurular (Değerlendiriliyor)</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold;">{funnel.get('Degerlendiriliyor', 0)}</td>
        <td style="padding:8px 12px; text-align:right;">%{round(funnel.get('Degerlendiriliyor', 0)/total*100, 1) if total else 0}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;">🎯 Ön Elemeyi Geçenler</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold;">{funnel.get('On Eleme Gecti', 0)}</td>
        <td style="padding:8px 12px; text-align:right;">%{round(funnel.get('On Eleme Gecti', 0)/total*100, 1) if total else 0}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;">🎙️ Mülakata Çağrılanlar</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold;">{funnel.get('Mulakata Cagrildi', 0)}</td>
        <td style="padding:8px 12px; text-align:right;">Başvuru-Mülakat Oranı: %{analytics.get('app_to_interview_rate', 0)}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;">📨 Teklif Yapılanlar</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold;">{funnel.get('Teklif Yapildi', 0)}</td>
        <td style="padding:8px 12px; text-align:right;">Mülakat-Teklif Oranı: %{analytics.get('interview_to_offer_rate', 0)}</td>
      </tr>
      <tr style="background:#f0fdf4;">
        <td style="padding:8px 12px; font-weight:bold; color:#15803d;">🎉 İşe Alınanlar (İşe Başlama)</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold; color:#15803d;">{funnel.get('Ise Alindi', 0)}</td>
        <td style="padding:8px 12px; text-align:right; font-weight:bold; color:#15803d;">Teklif-Kabul Oranı: %{analytics.get('offer_to_hire_rate', 0)}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px; color:#64748b;">❌ Reddedilen Başvurular</td>
        <td style="padding:8px 12px; text-align:right; color:#64748b;">{funnel.get('Reddedildi', 0)}</td>
        <td style="padding:8px 12px; text-align:right; color:#64748b;">%{round(funnel.get('Reddedildi', 0)/total*100, 1) if total else 0}</td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">2. POZİSYON BAZLI BAŞVURU YOĞUNLUĞU</div>
  <table>
    <thead>
      <tr>
        <th>Pozisyon Adı</th>
        <th style="text-align:right;">Başvuru Sayısı</th>
        <th style="text-align:right;">Yüzde</th>
      </tr>
    </thead>
    <tbody>
      {pos_rows}
    </tbody>
  </table>

  <div style="margin-top: 36px; border-top: 1px dashed #cbd5e1; padding-top: 16px; display:flex; justify-content:space-between; font-family:sans-serif; font-size:0.85rem;">
    <div>
      <b>Raporlayan Yetkili:</b><br>
      İşe Alım &amp; Yetenek Kazanımı Uzmanı<br>
      İmza
    </div>
    <div style="text-align:right;">
      <b>İnceleyen ve Onaylayan:</b><br>
      İnsan Kaynakları Direktörü<br>
      Kaşe &amp; İmza
    </div>
  </div>
</div>

</body>
</html>"""

def generate_ik_csv_export(applications: List[Dict[str, Any]]) -> str:
    """
    Excel uyumlu UTF-8 with BOM CSV çıktısı üretir.
    """
    columns = [
        "Takip Kodu", "Adı Soyadı", "TCKN", "Telefon", "E-Posta",
        "Şehir", "Pozisyon", "Deneyim (Yıl)", "Eğitim Seviyesi",
        "Bölüm/Fakülte", "Maaş Beklentisi", "Teklif Maaşı", "İşe Başlama Tarihi",
        "Mülakat Skoru", "Mülakat Değerlendirmesi", "KEP Adresi", "Durum", "Başvuru Tarihi"
    ]

    lines = []
    lines.append(";".join(columns))

    for a in applications:
        row = [
            str(a.get("tracking_code", "")).replace(";", " "),
            str(a.get("full_name", "")).replace(";", " "),
            str(a.get("id_number", "")).replace(";", " "),
            str(a.get("phone", "")).replace(";", " "),
            str(a.get("email", "")).replace(";", " "),
            str(a.get("city", "")).replace(";", " "),
            str(a.get("position", "")).replace(";", " "),
            str(a.get("experience_years", "")).replace(";", " "),
            str(a.get("education_level", "")).replace(";", " "),
            str(a.get("school_department", "")).replace(";", " "),
            str(a.get("salary_expectation", "")).replace(";", " "),
            str(a.get("offer_salary", "")).replace(";", " "),
            str(a.get("offer_start_date", "")).replace(";", " "),
            str(a.get("interview_score", "")).replace(";", " "),
            str(a.get("interview_rating", "")).replace(";", " "),
            str(a.get("kep_address", "")).replace(";", " "),
            str(a.get("status", "")).replace(";", " "),
            str(a.get("created_at", "")).replace(";", " ")
        ]
        lines.append(";".join(row))

    return "\ufeff" + "\r\n".join(lines)
