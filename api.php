<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=UTF-8");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$dataFile = __DIR__ . '/ik_basvurular.json';

function getStoredData($file) {
    if (!file_exists($file)) return [];
    $content = file_get_contents($file);
    return json_decode($content, true) ?: [];
}

function saveStoredData($file, $data) {
    file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

function validateKepAddress($kep) {
    $kep = trim((string)$kep);
    if (empty($kep)) return ['valid' => false, 'error' => 'KEP adresi boş bırakılamaz.'];
    if (!preg_match('/^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.kep\.tr$/i', $kep)) {
        return ['valid' => false, 'error' => 'Geçersiz KEP formatı. Adres ".kep.tr" ile bitmelidir.'];
    }
    return ['valid' => true, 'kep' => strtolower($kep), 'provider' => explode('@', $kep)[1] ?? ''];
}

function generateJobOfferText($candidate, $offerData) {
    $candName = $candidate['full_name'] ?? 'Değerli Aday';
    $tckn = $candidate['id_number'] ?? 'TR';
    $position = $candidate['position'] ?? 'Uzman';
    $salary = $offerData['salary'] ?? 'Görüşülen Tutar';
    $startDate = $offerData['start_date'] ?? date('Y-m-d', strtotime('+14 days'));
    $compName = $offerData['company_name'] ?? 'Akıllı Kurumsal Çözümler A.Ş.';
    $compKep = $offerData['company_kep'] ?? 'ik@kurumsal.kep.tr';
    $candKep = !empty($offerData['candidate_kep']) ? $offerData['candidate_kep'] : ($candidate['kep_address'] ?? 'Belirtilmedi');
    $probation = $offerData['probation_period'] ?? '2 Ay';
    $dateStr = date('d.m.Y');
    $tracking = $candidate['tracking_code'] ?? ('IK-OFFER-' . rand(1000, 9999));

    return "======================================================================\n" .
           "T.C. 4857 SAYILI İŞ KANUNU VE 5070 SAYILI ELEKTRONİK İMZA KANUNU UYARINCA\n" .
           "RESMİ İŞ VE ÇALIŞMA TEKLİFİ (KAYITLI ELEKTRONİK POSTA / KEP METNİ)\n" .
           "======================================================================\n\n" .
           "Tarih           : {$dateStr}\n" .
           "Referans / Takip: {$tracking}\n" .
           "Gönderici       : {$compName}\n" .
           "Şirket KEP      : {$compKep}\n\n" .
           "Sayın           : {$candName}\n" .
           "T.C. Kimlik No  : {$tckn}\n" .
           "Aday KEP Adresi : {$candKep}\n\n" .
           "Şirketimiz bünyesinde açık bulunan pozisyona ilişkin başvurunuz ve insan kaynakları\n" .
           "değerlendirme süreçleri başarıyla sonuçlanmıştır. Tarafınıza aşağıdaki şartlar dahilinde\n" .
           "iş teklifinde bulunmaktan memnuniyet duymaktayız:\n\n" .
           "1. Pozisyon ve Görev Tanımı   : {$position}\n" .
           "2. İşe Başlama Tarihi         : {$startDate}\n" .
           "3. Net Aylık Ücret / Maaş     : {$salary}\n" .
           "4. Deneme Süresi              : {$probation} (4857 Sayılı Kanun Madde 15)\n" .
           "5. Çalışma Şekli              : Tam Zamanlı / Hibrit\n" .
           "6. Yan Haklar                 : Yemek Kartı, Özel Sağlık Sigortası, Yol/Ulaşım Desteği\n\n" .
           "YASAL VE HUKUKİ BİLGİLENDİRME:\n" .
           "İşbu teklif mektubu, 5070 sayılı Elektronik İmza Kanunu ve Kayıtlı Elektronik Posta (KEP)\n" .
           "Sistemine İlişkin Usul ve Esaslar Hakkında Yönetmelik hükümleri uyarınca güvenli elektronik imza\n" .
           "ile onaylanarak BTK lisanslı KEPHS altyapısı üzerinden delil kaydı ile iletilebilir.\n\n" .
           "Bu teklifi kabul ettiğinize dair beyanınızı en geç 5 (beş) iş günü içerisinde şirket KEP\n" .
           "adresimize ({$compKep}) veya sistem üzerinden yanıtlamanızı rica ederiz.\n\n" .
           "Saygılarımızla,\n" .
           "{$compName} - İnsan Kaynakları Direktörlüğü\n";
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'POST') {
    $raw = file_get_contents('php://input');
    $input = json_decode($raw, true) ?: [];

    // KEP & E-İmza İş Teklifi Oluşturma
    if ($action === 'teklif-olustur' || (isset($input['action']) && $input['action'] === 'teklif-olustur')) {
        $tracking = $input['tracking_code'] ?? '';
        $records = getStoredData($dataFile);
        $found = null;
        $foundIdx = -1;

        foreach ($records as $idx => $r) {
            if (($r['tracking_code'] ?? '') === $tracking) {
                $found = $r;
                $foundIdx = $idx;
                break;
            }
        }

        if (!$found) {
            http_response_code(404);
            echo json_encode(['error' => 'Aday kaydı bulunamadı.']);
            exit();
        }

        $letter = generateJobOfferText($found, $input);
        $records[$foundIdx]['status'] = 'Teklif Yapildi';
        $records[$foundIdx]['offer_salary'] = $input['salary'] ?? '';
        $records[$foundIdx]['offer_start_date'] = $input['start_date'] ?? '';
        $records[$foundIdx]['offer_letter_text'] = $letter;
        if (!empty($input['candidate_kep'])) {
            $records[$foundIdx]['kep_address'] = $input['candidate_kep'];
        }

        saveStoredData($dataFile, $records);
        echo json_encode([
            'status' => 'success',
            'tracking_code' => $tracking,
            'offer_letter' => $letter,
            'new_status' => 'Teklif Yapildi'
        ], JSON_UNESCAPED_UNICODE);
        exit();
    }

    // Durum Güncelleme
    if ($action === 'durum-guncelle' || (isset($input['action']) && $input['action'] === 'durum-guncelle')) {
        $tracking = $input['tracking_code'] ?? '';
        $newStatus = $input['status'] ?? 'Degerlendiriliyor';

        $records = getStoredData($dataFile);
        $updated = false;
        foreach ($records as &$item) {
            if (($item['tracking_code'] ?? '') === $tracking) {
                $item['status'] = $newStatus;
                $updated = true;
                break;
            }
        }
        saveStoredData($dataFile, $records);
        echo json_encode(['status' => 'success', 'updated' => $updated, 'new_status' => $newStatus]);
        exit();
    }

    // Default POST: Yeni Başvuru
    $trackingCode = $input['tracking_code'] ?? ('BASVURU-2026-' . rand(1000, 9999));
    $input['tracking_code'] = $trackingCode;
    $input['status'] = $input['status'] ?? 'Degerlendiriliyor';
    $input['created_at'] = $input['created_at'] ?? date('c');

    $records = getStoredData($dataFile);
    array_unshift($records, $input);
    saveStoredData($dataFile, $records);

    echo json_encode(['status' => 'success', 'tracking_code' => $trackingCode]);
    exit();
}

if ($method === 'GET') {
    $records = getStoredData($dataFile);

    if ($action === 'validate-kep') {
        $kep = $_GET['kep'] ?? '';
        echo json_encode(validateKepAddress($kep), JSON_UNESCAPED_UNICODE);
        exit();
    }

    if ($action === 'teklif-goruntule') {
        $tracking = $_GET['tracking_code'] ?? '';
        foreach ($records as $r) {
            if (($r['tracking_code'] ?? '') === $tracking) {
                echo json_encode([
                    'status' => 'success',
                    'tracking_code' => $tracking,
                    'candidate_name' => $r['full_name'] ?? '',
                    'position' => $r['position'] ?? '',
                    'offer_salary' => $r['offer_salary'] ?? '',
                    'offer_start_date' => $r['offer_start_date'] ?? '',
                    'offer_letter_text' => $r['offer_letter_text'] ?? ''
                ], JSON_UNESCAPED_UNICODE);
                exit();
            }
        }
        http_response_code(404);
        echo json_encode(['error' => 'Teklif kaydı bulunamadı.']);
        exit();
    }

    if ($action === 'istatistikler') {
        $total = count($records);
        $by_status = [];
        $by_pos = [];
        foreach ($records as $r) {
            $st = $r['status'] ?? 'Degerlendiriliyor';
            $by_status[$st] = ($by_status[$st] ?? 0) + 1;
            $pos = $r['position'] ?? 'Diger';
            $by_pos[$pos] = ($by_pos[$pos] ?? 0) + 1;
        }
        echo json_encode(['total' => $total, 'by_status' => $by_status, 'by_position' => $by_pos]);
        exit();
    }

    echo json_encode($records, JSON_UNESCAPED_UNICODE);
    exit();
}
