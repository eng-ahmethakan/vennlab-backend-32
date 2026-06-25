# VennLab AI – Kurulum ve Kullanım Kılavuzu

## Proje Yapısı

```
vennlab/
├── vennlab_frontend.html      ← Mevcut HTML (değiştirilmiş AI sekmesi)
├── backend/
│   ├── main.py                ← FastAPI uygulaması
│   ├── requirements.txt       ← Python bağımlılıkları
│   ├── .env.example           ← .env şablonu (API key buraya)
│   └── .gitignore
└── README.md
```

## Mimari

```
Kullanıcı
   │  doğal dil komutu
   ▼
vennlab_frontend.html
   │  POST /ai/command  {user_prompt, snapshot}
   ▼
FastAPI Backend (main.py)
   │  Gemini API çağrısı (API key .env'den okunur)
   ▼
Gemini 2.5 Flash
   │  JSON actions
   ▼
Backend → Frontend
   │  actions uygulanır
   ▼
VennLab grafiği güncellenir
```

**Frontend'de API key kesinlikle bulunmaz.**

---

## 1. Backend Kurulumu

### Gereksinimler
- Python 3.11+
- Gemini API key ([Google AI Studio](https://aistudio.google.com/app/apikey))

### Adımlar

```bash
# 1. Backend klasörüne gir
cd backend

# 2. Sanal ortam oluştur
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. .env dosyasını oluştur
cp .env.example .env
# .env dosyasını aç ve GEMINI_API_KEY'i doldur:
#   GEMINI_API_KEY=AIzaSy_GERCEK_ANAHTARINIZ

# 5. Backend'i başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend çalıştığında: http://localhost:8000/health adresine giderek test edin.

Beklenen yanıt:
```json
{"status":"ok","model":"gemini-2.5-flash","api_key_loaded":true}
```

---

## 2. Frontend Kullanımı

1. `vennlab_frontend.html` dosyasını tarayıcıda açın
2. **AI** sekmesine gidin
3. Backend URL doğruysa (`http://localhost:8000`) **Bağlantıyı Test Et** butonuna tıklayın
4. Yeşil "Bağlı" göstergesi görünmeli

---

## 3. Örnek Komutlar

| Komut | Ne Yapar |
|---|---|
| `grafik 1 kırmızı yap` | 1. listenin rengini kırmızı yapar |
| `grafik 2 sayılarını göster` | Sayı etiketlerini görünür yapar |
| `grafik başlığını Şekil 1 yap` | Başlık metnini günceller |
| `A ve B kesişimini göster` | A∩B kesişim bölgesini filtreler |
| `akademik makale formatına getir` | Beyaz arka plan, Times New Roman, academic palet |
| `UpSet grafiği oluştur` | Grafik tipini UpSet'e çevirir |
| `akademik rapor oluştur` | Analiz raporu üretir |
| `tüm ortak elemanları göster` | Tüm listelerde bulunanları filtreler |
| `koyu temaya geç` | Dark mode uygular |
| `sayıları gizle` | Kesişim sayılarını gizler |

---

## 4. API Endpoint'leri

### `GET /health`
Backend ve API key durumunu kontrol eder.

### `POST /ai/command`
```json
// İstek
{
  "user_prompt": "1. listeyi kırmızı yap",
  "snapshot": {
    "chart": {"type": "venn", "title": "..."},
    "lists": [{"index": 0, "name": "A", "count": 10}],
    "totals": {...},
    "topRegions": [...],
    "pairwise": [...]
  }
}

// Yanıt
{
  "answer": "1. listenin rengi kırmızıya (#ff3b5c) değiştirildi.",
  "report": "",
  "actions": [
    {"type": "setListStyle", "index": 0, "color": "#ff3b5c"}
  ]
}
```

### Action Tipleri

| Action | Parametreler |
|---|---|
| `setViz` | `value`: venn\|upset\|heatmap\|pairwise\|flower\|edwards |
| `setTitle` | `value`: başlık metni |
| `setTheme` | `value`: light\|dark |
| `setPalette` | `value`: modern\|academic\|pastel\|contrast |
| `setShowCounts` | `value`: true\|false |
| `setShowLabels` | `value`: true\|false |
| `setFont` | `family`, `size`, `weight`, `style` |
| `setColors` | `background`, `text`, `count` (hex) |
| `setShape` | `fillOpacity` (10–80), `strokeWidth` (1–8) |
| `setListStyle` | `index`, `name`, `color`, `labelColor`, `labelSize` |
| `showFilter` | `mode`, `k`, `listIndex` |
| `makeReport` | – |

---

## 5. Production Dağıtımı

### CORS Ayarı
`main.py` içinde `allow_origins=["*"]` kısmını kendi domain'inize daraltın:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],
    ...
)
```

### Frontend URL Güncelleme
Production'da `vennlab_frontend.html` içindeki varsayılan backend URL'ini (`http://localhost:8000`) production backend URL'inize göre güncelleyin.

### Güvenlik Notları
- `.env` dosyasını asla git'e commit etmeyin
- Production'da HTTPS kullanın
- Gerekirse rate limiting ekleyin (`slowapi` paketi)

---

## 6. Sorun Giderme

**Backend başlamıyor:**
- `.env` dosyasının var olduğunu kontrol edin
- `GEMINI_API_KEY` değerinin boş olmadığını kontrol edin

**"Backend bağlantısı yok" hatası:**
- `uvicorn` çalışıyor mu? Terminal'de kontrol edin
- Backend URL doğru mu? (`http://localhost:8000`)
- Tarayıcı konsolu (F12) ile CORS hatası var mı?

**"API key geçersiz" hatası:**
- [Google AI Studio](https://aistudio.google.com) → API Keys → yeni key oluşturun
- `.env` dosyasına yapıştırın ve backend'i yeniden başlatın

**Gemini yanıt vermiyor:**
- Model adını `gemini-1.5-flash` olarak değiştirip deneyin (`.env`'de `GEMINI_MODEL`)
