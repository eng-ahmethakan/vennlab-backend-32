"""
VennLab AI Backend – FastAPI + Gemini
API key yalnızca burada .env dosyasından okunur, frontend'e asla gönderilmez.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), encoding='utf-8-sig')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = FastAPI(title="VennLab AI Backend", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
# Geliştirme ortamında tüm originlere izin verilir.
# Production'da bunu kendi domain'inize daraltın:
#   allow_origins=["https://yourapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── Pydantic modelleri ─────────────────────────────────────────────────────────
class VennSnapshot(BaseModel):
    chart: dict = {}
    lists: list = []
    totals: dict = {}
    allCommon: list = []
    topRegions: list = []
    pairwise: list = []

class AIRequest(BaseModel):
    user_prompt: str
    snapshot: Optional[VennSnapshot] = None

class AIResponse(BaseModel):
    answer: str
    report: str
    actions: list[dict]

# ── System prompt ──────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    return """Sen VennLab Pro içinde çalışan bir yapay zeka asistanısın. Kullanıcı Türkçe konuşur.

Görevlerin:
1. Venn grafiğinin görsel stilini değiştirmek (renk, font, şekil, tema, palet)
2. Liste renklerini ve adlarını değiştirmek
3. Grafik türünü değiştirmek veya önermek
4. Filtreler çalıştırmak (ortak, benzersiz, belirli kesişimler)
5. Grafik başlığını güncellemek
6. Akademik/teknik analiz raporu yazmak
7. Sayıları ve etiketleri gösterip gizlemek

SADECE geçerli JSON döndür. Markdown, kod bloğu veya ek açıklama KULLANMA.
Tam şema:
{
  "answer": "Kullanıcıya kısa Türkçe yanıt – ne yaptığını açıkla",
  "report": "Varsa detaylı rapor metni, yoksa boş string",
  "actions": [{"type": "..."}]
}

İzinli action tipleri ve şemaları:
- {"type":"setViz", "value":"venn|upset|heatmap|pairwise|flower|edwards"}
- {"type":"setTitle", "value":"Başlık metni"}
- {"type":"setTheme", "value":"light|dark"}
- {"type":"setPalette", "value":"modern|academic|pastel|contrast"}
- {"type":"setWhiteExport", "value":true}
- {"type":"setShowCounts", "value":true}
- {"type":"setShowLabels", "value":true}
- {"type":"setFont", "family":"Arial|Times New Roman|Georgia|Verdana|Inter|Monospace", "size":12, "weight":"400|600|800|900", "style":"normal|italic"}
- {"type":"setColors", "background":"#ffffff", "text":"#111827", "count":"#000000"}
- {"type":"setShape", "fillOpacity":38, "strokeWidth":3}
- {"type":"setListStyle", "index":0, "name":"Ad", "color":"#ff0000", "labelColor":"#ffffff", "labelSize":12, "fontWeight":"800", "fontFamily":"Arial", "fontStyle":"normal"}
- {"type":"showFilter", "mode":"allCommon|allUnique|exactK|atLeastK|listOnly|listAll", "k":2, "listIndex":0}
- {"type":"makeReport"}

Özel kurallar:
- Renkler mutlaka hex formatında (#rrggbb) olsun
- Liste index'leri 0'dan başlar (1. liste = index 0)
- "kırmızı"→#ff3b5c, "mavi"→#2f80ed, "yeşil"→#00a66c, "sarı"→#ffd166, "turuncu"→#ff9f40, "mor"→#8a5cff, "pembe"→#ff6fb1
- Akademik format: light tema + Times New Roman + academic palet + white export
- Grafik tipi önerisi: 2-3 liste → venn, 4+ liste → upset
- Rapor istenirse "report" alanını Türkçe ve ayrıntılı doldur
- Sadece izinli action tiplerini kullan
- Yanıt (answer) kısa ve net olsun
"""

# ── Gemini API çağrısı ─────────────────────────────────────────────────────────
import asyncio

async def call_gemini(user_prompt: str, snapshot_dict: dict) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY .env dosyasında tanımlı değil.")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "systemInstruction": {"parts": [{"text": build_system_prompt()}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps({"userRequest": user_prompt, "vennlab": snapshot_dict}, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }

    for attempt in range(3):  # 3 deneme
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code == 503:
            wait = (attempt + 1) * 3  # 3s, 6s, 9s
            await asyncio.sleep(wait)
            continue

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Gemini API hatası: {resp.text[:500]}")

        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip() or "{}"

    raise HTTPException(status_code=503, detail="Gemini şu an yoğun. Lütfen birkaç saniye bekleyip tekrar deneyin.")
# ── Endpoint'ler ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Backend'in ayakta olduğunu ve API key'in yüklendiğini doğrular."""
    return {
        "status": "ok",
        "model": GEMINI_MODEL,
        "api_key_loaded": bool(GEMINI_API_KEY),
    }

@app.post("/ai/command", response_model=AIResponse)
async def ai_command(req: AIRequest):
    """
    Kullanıcı komutunu Gemini'ye gönderir, JSON action listesi olarak döner.
    Frontend bu action'ları uygulayarak VennLab grafiğini günceller.
    """
    if not req.user_prompt.strip():
        raise HTTPException(status_code=400, detail="user_prompt boş olamaz.")

    snapshot_dict = req.snapshot.model_dump() if req.snapshot else {}

    raw = await call_gemini(req.user_prompt, snapshot_dict)

    # Gemini bazen markdown sarmalı döndürebilir – temizle
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        clean = clean.rsplit("```", 1)[0].strip()

    try:
        obj = json.loads(clean)
    except json.JSONDecodeError:
        obj = {"answer": clean, "report": "", "actions": []}

    return AIResponse(
        answer=obj.get("answer", "İşlem tamamlandı."),
        report=obj.get("report", ""),
        actions=obj.get("actions", []),
    )

@app.post("/ai/report")
async def ai_report(req: AIRequest):
    """Sadece analiz raporu üretir (actions döndürmez)."""
    req.user_prompt = "Bu Venn analizinden detaylı akademik bir rapor oluştur."
    result = await ai_command(req)
    return {"report": result.report or result.answer}
