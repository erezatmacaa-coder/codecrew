# CodeCrew

**Multi-Agent Kod Geliştirme Sistemi** — 8 yapay zeka ajanı bir ofiste birlikte çalışır, kod yazar ve projeleri tamamlar.

## Özellikler

- **8 Uzman Ajan**: Alp (lider), Cem (geliştirici), Rusty (code review), Testo (test), Bug (hata avcısı), Devina (DevOps), Doc (dokümantasyon), Ideator (yaratıcı fikirler)
- **CLI & Web UI**: Terminalden veya tarayıcıdan kullan
- **3D Ofis**: Three.js ile 3 boyutlu ofis ortamı
- **Tool Desteği**: Dosya okuma/yazma, shell komutları
- **Groq API**: Ücretsiz API ile çalışır

## Kurulum

```bash
git clone https://github.com/erezatmacaa-coder/codecrew.git
cd codecrew
pip install -r requirements.txt
echo "API_KEY=your_groq_api_key" > .env
python main.py
```

Web arayüzü:
```bash
python -m uvicorn web_app:app --host 0.0.0.0 --port 8000
```
