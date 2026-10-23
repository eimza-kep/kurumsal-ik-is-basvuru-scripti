# -*- coding: utf-8 -*-
"""
ik_onboarding_engine.py
-----------------------
Kurumsal İK İşe Alım, KEP Resmi Teklif Mektubu ve CV Önizleme Motoru.
4857 Sayılı İş Kanunu ve BTK KEP Standartları ile tam uyumlu.
"""

import re
import datetime
from typing import Dict, Any, Optional

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
    resmi iş teklifi ve işe başlama mektubunu üretir.
    """
    name = candidate.get("full_name", "Sayın Aday")
    position = candidate.get("position", "Belirtilmemiş Pozisyon")
    tc = candidate.get("id_number", "TCKN")
    kep = candidate.get("kep_address") or offer_data.get("candidate_kep", "Belirtilmedi")
    
    company_name = offer_data.get("company_name", "Şirketimiz A.Ş.")
    company_kep = offer_data.get("company_kep", "ik@hs01.kep.tr")
    salary = offer_data.get("salary", candidate.get("salary_expectation", "Piyasa Koşulları"))
    start_date = offer_data.get("start_date", datetime.date.today().strftime("%d.%m.%Y"))
    benefits = offer_data.get("benefits", "Yol, Yemek (Multinet), Özel Sağlık Sigortası, Yıllık Prim")

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
