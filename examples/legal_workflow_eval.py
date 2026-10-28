#!/usr/bin/env python3
"""Run three direct Gemma 4 12B legal-workflow tests and create a short PDF."""
from __future__ import annotations
import argparse, html, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT.parent / "Nepali_AI_VOICE_RAG/ollama/MODEL_ANSWER_APPENDIX.pdf"
DEFAULT_OUTPUT = ROOT / "outputs/gemma4_12b_legal_tests.pdf"
SYSTEM_PROMPT = """तपाईं नेपाली कानुनी कागजात खोज, सारांश र मस्यौदा तयार गर्ने सहायक हुनुहुन्छ। सधैँ नेपाली देवनागरीमा सीधा, स्पष्ट र तथ्यपरक उत्तर दिनुहोस्। दिइएको सन्दर्भ वा डाटामा आधारित भएर मात्र उत्तर दिनुहोस्; नदिइएको तथ्य, मिति, रकम, कानुन वा घटना नथप्नुहोस्। आवश्यक विवरण नभए अङ्ग्रेजी camelCase मा {{placeholderName}} राख्नुहोस्। प्रश्न नसोध्नुहोस्। मागिएको अन्तिम उत्तर वा कागजात मात्र फर्काउनुहोस्; भूमिका, परिचय, मूल्याङ्कन वा टिप्पणी नथप्नुहोस्।""".strip()

def env_values():
    values = dict(os.environ)
    for path in (ROOT / ".env", ROOT.parent / "nepali-chat-demo/backend/.env"):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    key, value = line.split("=", 1)
                    values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values

def extract_pdf(path):
    result = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True)
    return re.sub(r"\n{3,}", "\n\n", result.stdout)

def retrieve(text, query, count=2):
    size, overlap = 3200, 300
    parts = [text[i:i + size] for i in range(0, len(text), size - overlap)]
    terms = {w.lower() for w in re.findall(r"[\w\u0900-\u097f]+", query) if len(w) > 2}
    parts.sort(key=lambda p: sum(p.lower().count(term) for term in terms), reverse=True)
    return "\n\n".join(f"[स्रोत अंश {i}]\n{part}" for i, part in enumerate(parts[:count], 1))

def generate(url, key, user_prompt):
    payload = {"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
               "temperature": 0.15, "top_p": 0.9, "top_k": 40, "max_tokens": 3000}
    request = Request(url, data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    for attempt in range(12):
        try:
            with urlopen(request, timeout=900) as response:
                answer = json.loads(response.read()).get("response", "").strip()
            break
        except HTTPError as error:
            if error.code != 503 or attempt == 11:
                raise
            print("Model busy; retrying in 10 seconds...", flush=True)
            time.sleep(10)
    return answer or "उत्तर प्राप्त भएन।"

def make_pdf(results, output):
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    sections = []
    for title, query, answer in results:
        sections.append(f"<section><h2>{html.escape(title)}</h2><h3>प्रयोगकर्ता प्रश्न</h3><div class='box'>{html.escape(query)}</div>"
                        f"<h3>Gemma 4 12B उत्तर</h3><div class='answer'>{html.escape(answer)}</div></section>")
    page = f"""<!doctype html><html lang="ne"><head><meta charset="utf-8"><style>
@page {{size:A4;margin:18mm}} body{{font-family:'Noto Sans Devanagari',sans-serif;color:#17202a;line-height:1.55}}
h1{{font-size:21px}} h2{{font-size:17px;color:#17365d;margin-top:24px}} h3{{font-size:12px;margin:12px 0 5px}}
.box,.answer{{white-space:pre-wrap;font-size:10.5pt;padding:9px;background:#f5f7f9}} .answer{{background:white;border-left:3px solid #315f8c}}
section{{break-before:page}} section:first-of-type{{break-before:auto}}</style></head>
<body><h1>Gemma 4 12B — कानुनी कार्य परीक्षण</h1>{''.join(sections)}</body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "report.html"
        source.write_text(page, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--no-pdf-header-footer",
                        f"--print-to-pdf={output.resolve()}", source.as_uri()], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    env = env_values(); key = env.get("LLM_API_KEY", "")
    if not key: raise RuntimeError("LLM_API_KEY is missing")
    url = env.get("LLM_API_URL", "https://tipoff-entryway-obedience.ngrok-free.dev").rstrip("/")
    if not url.endswith("/v1/generate"): url += "/v1/generate"
    search = "यस PDF मा Gemma 4 12B को कानुनी मस्यौदा परीक्षणमा देखिएका मुख्य नतिजा र कमजोरीको छोटो सारांश दिनुहोस्।"
    letter = "रु. २,५०,००० करार रकम भुक्तानीका लागि औपचारिक मागपत्र तयार गर्नुहोस्। पठाउने सुमन श्रेष्ठ, ललितपुर महानगरपालिका वडा नं. ३ र प्राप्तकर्ता रवि थापा, भक्तपुर नगरपालिका वडा नं. ५ हुन्। करार मिति २०८२ वैशाख १० गते हो। पत्रको मिति र भुक्तानीको अन्तिम मिति उपलब्ध छैन; प्लेसहोल्डर राख्नुहोस्।"
    case = "केस डाटाको छोटो तथ्यपरक सारांश तयार गर्नुहोस्: वादीको दाबी रु. ५०,००० बक्यौता; प्रतिवादीले २०८२ असार ५ गते रु. २०,००० भुक्तानी गरेको जनाएको; बाँकी रकमबारे अतिरिक्त विवरण, मुद्दा नम्बर र पक्षहरूको ठेगाना उपलब्ध छैन।"
    tests = [("१. PDF खोजको सारांश (RAG शैली)", search, f"{search}\n\nPDF बाट खोजिएका अंश:\n{retrieve(extract_pdf(args.pdf), search)}"),
             ("२. कानुनी पत्र तयारी", letter, letter), ("३. केस डाटाको सारांश", case, case)]
    results=[]
    for i,(title,shown,prompt) in enumerate(tests,1):
        print(f"[{i}/3] {title}", flush=True); results.append((title,shown,generate(url,key,prompt)))
    make_pdf(results,args.output); print(f"Saved: {args.output.resolve()}")

if __name__ == "__main__": main()
