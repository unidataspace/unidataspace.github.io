\
from __future__ import annotations
import csv, json, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "site_template"
OUT_DIR = ROOT / "site"

def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^0-9a-z\-가-힣]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "item"

def read_config() -> dict:
    return json.loads((TEMPLATE_DIR / "config.json").read_text(encoding="utf-8"))

def read_template() -> str:
    return (TEMPLATE_DIR / "template.html").read_text(encoding="utf-8")

def pick_csv_path() -> Path:
    real = DATA_DIR / "source.csv"
    return real if real.exists() else (DATA_DIR / "parking_sample.csv")

def normalize_headers(headers: list[str]) -> dict[str, int]:
    norm = {}
    for i, h in enumerate(headers):
        hh = (h or "").strip()
        hlow = hh.lower()
        if any(k in hh for k in ["주차장명","시설명"]) or hlow in ["name","parking_name","prk_nm"]:
            norm.setdefault("name", i)
        if any(k in hh for k in ["도로명주소","지번주소","주소","소재지"]) or hlow in ["address","addr","location"]:
            if "도로명" in hh:
                norm["address"] = i
            else:
                norm.setdefault("address", i)
        if any(k in hh for k in ["시도명","시군구명","시도","광역","지역"]) or hlow in ["region","sido","sigungu"]:
            norm.setdefault("region", i)
        if any(k in hh for k in ["주차장유형","유형","구분"]) or hlow in ["type","parking_type"]:
            norm.setdefault("type", i)
        if "위도" in hh or hlow in ["lat","latitude"]:
            norm.setdefault("lat", i)
        if "경도" in hh or hlow in ["lon","lng","longitude"]:
            norm.setdefault("lon", i)
        if any(k in hh for k in ["관리기관","제공기관","기관","운영기관"]) or hlow in ["org","organization"]:
            norm.setdefault("org", i)
        if any(k in hh for k in ["전화","연락처","tel"]) or hlow in ["phone","tel"]:
            norm.setdefault("phone", i)
    return norm

def load_items(csv_path: Path) -> list[dict]:
    def open_csv_any_encoding(csv_path):
    # UTF-8 우선, 안 되면 CP949/EUC-KR로 재시도
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return open(csv_path, "r", encoding=enc, newline="")
        except UnicodeDecodeError:
            continue
    # 마지막: 그래도 안 되면 예외 발생
    return open(csv_path, "r", encoding="utf-8", errors="strict", newline="")

with open_csv_any_encoding(csv_path) as f:

        reader = csv.reader(f)
        headers = next(reader, [])
        if not headers:
            return []
        m = normalize_headers(headers)

        def get(row, key):
            idx = m.get(key, None)
            if idx is None or idx >= len(row):
                return ""
            return (row[idx] or "").strip()

        items = []
        for row in reader:
            name = get(row, "name") or "(이름 미상)"
            address = get(row, "address")
            region = get(row, "region") or (address.split()[0] if address else "기타")
            ptype = get(row, "type") or "정보없음"
            lat = get(row, "lat")
            lon = get(row, "lon")
            org = get(row, "org")
            phone = get(row, "phone")

            raw = f"{region}|{name}|{address}|{lat}|{lon}"
            pid = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]

            items.append({
                "id": pid,
                "name": name,
                "address": address,
                "region": region,
                "type": ptype,
                "lat": lat,
                "lon": lon,
                "org": org,
                "phone": phone,
            })
        return items

def adsense(cfg: dict) -> dict:
    client = (cfg.get("adsense_client") or "").strip()
    if not client:
        return {"head":"","top":"","bottom":""}
    head = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" crossorigin="anonymous"></script>'
    def block(slot):
        slot = (slot or "").strip()
        if not slot:
            return ""
        return f"""
<div class="card">
  <ins class="adsbygoogle" style="display:block"
       data-ad-client="{client}" data-ad-slot="{slot}"
       data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>
""".strip()
    return {"head":head, "top": block(cfg.get("adsense_slot_top","")), "bottom": block(cfg.get("adsense_slot_bottom",""))}

def render(tpl: str, cfg: dict, title: str, desc: str, content: str) -> str:
    ad = adsense(cfg)
    html = tpl
    for k,v in {
        "{{TITLE}}": title,
        "{{DESC}}": desc,
        "{{SITE_NAME}}": cfg.get("site_name",""),
        "{{SITE_TAGLINE}}": cfg.get("site_tagline",""),
        "{{FOOTER_SOURCE}}": cfg.get("footer_source",""),
        "{{ADSENSE_HEAD}}": ad["head"],
        "{{ADSENSE_TOP}}": ad["top"],
        "{{ADSENSE_BOTTOM}}": ad["bottom"],
        "{{CONTENT}}": content,
    }.items():
        html = html.replace(k, v)
    return html

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def copy_assets():
    (OUT_DIR/"assets").mkdir(parents=True, exist_ok=True)
    for p in (TEMPLATE_DIR/"assets").glob("*"):
        if p.is_file():
            (OUT_DIR/"assets"/p.name).write_bytes(p.read_bytes())

def build_index(cfg, tpl, items):
    regions = sorted({it["region"] for it in items})
    region_opts = "\n".join([f'<option value="{r}">{r}</option>' for r in regions])
    region_btns = "\n".join([f'<a class="btn" href="/regions/{slugify(r)}/">{r}</a>' for r in regions[:60]])

    content = """
<div class="card">
  <h1 class="h1">{{H1}}</h1>
  <div class="notice">
    키워드를 입력하면 이름/주소/기관 기준으로 필터링됩니다.
    (실데이터를 넣으면 전국 단위로 동작합니다.)
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2 class="h2">검색</h2>
    <input id="q" class="input" placeholder="예: 서울 중구 / 부산역 / 태화강 / 주차장명..." />
    <div style="height:10px"></div>
    <select id="region" class="input">
      <option value="">전체 지역</option>
      {{REGION_OPTIONS}}
    </select>
    <div style="height:12px"></div>
    <div class="muted small" id="count"></div>
    <div style="height:10px"></div>
    <table class="table" id="tbl">
      <thead><tr><th>이름</th><th>주소</th><th>유형</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="card">
    <h2 class="h2">지역별 바로가기</h2>
    <div class="btnrow">
      {{REGION_BTNS}}
    </div>
    <div style="height:12px"></div>
    <div class="muted small">지역이 너무 많으면 일부만 표시됩니다.</div>
  </div>
</div>

<script>
async function main(){
  const res = await fetch('/data/parking.json');
  const items = await res.json();

  const q = document.getElementById('q');
  const region = document.getElementById('region');
  const tbody = document.querySelector('#tbl tbody');
  const count = document.getElementById('count');

  function esc(s){return (s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}

  function render(){
    const qq = (q.value||'').trim().toLowerCase();
    const rr = region.value;
    const filtered = items.filter(it => {
      if (rr && it.region !== rr) return false;
      if (!qq) return true;
      const hay = (it.name + ' ' + it.address + ' ' + it.org).toLowerCase();
      return hay.includes(qq);
    }).slice(0, 200);

    count.textContent = '결과: ' + filtered.length + '개 (최대 200개 표시)';
    tbody.innerHTML = filtered.map(it => `
      <tr>
        <td><a href="/p/${it.id}/">${esc(it.name)}</a><div class="badge">${esc(it.region)}</div></td>
        <td>${esc(it.address||'')}</td>
        <td>${esc(it.type||'')}</td>
      </tr>
    `).join('');
  }

  q.addEventListener('input', render);
  region.addEventListener('change', render);
  render();
}
main();
</script>
""".replace("{{H1}}", cfg.get("site_name","")).replace("{{REGION_OPTIONS}}", region_opts).replace("{{REGION_BTNS}}", region_btns)

    write(OUT_DIR/"index.html", render(tpl, cfg, cfg.get("site_name",""), cfg.get("site_tagline",""), content))

def build_about(cfg, tpl, csv_path, items):
    content = f"""
<div class="card">
  <h1 class="h1">소개</h1>
  <p class="notice">
    이 사이트는 공공데이터를 “검색하기 쉽게 정리”해서 보여주는 초미니 서비스입니다.<br/>
    현재 데이터 파일: <b>{csv_path.name}</b> / 레코드 수: <b>{len(items)}</b>
  </p>
  <div class="card">
    <div class="notice">
      ✅ 운영 팁<br/>
      - 실데이터: <code>data/source.csv</code>로 업로드하면 자동 반영됩니다.<br/>
      - 출처표시/이용허락범위 표기를 꼭 확인하고 푸터에 출처를 남기세요.<br/>
      - 광고를 붙이면 '얇은 페이지 남발'로 보이지 않도록 정보 품질을 유지하세요.
    </div>
  </div>
</div>
"""
    write(OUT_DIR/"about/index.html", render(tpl, cfg, f"소개 | {cfg.get('site_name','')}", "사이트 소개", content))

def build_regions(cfg, tpl, items):
    by = {}
    for it in items:
        by.setdefault(it["region"], []).append(it)
    region_list = sorted(by.keys())

    btns = "\n".join([f'<a class="btn" href="/regions/{slugify(r)}/">{r} <span class="muted">({len(by[r])})</span></a>' for r in region_list])
    content = f"""
<div class="card">
  <h1 class="h1">지역별</h1>
  <p class="notice">지역을 클릭하면 해당 지역의 공영주차장 목록을 볼 수 있습니다.</p>
  <div class="btnrow">
    {btns}
  </div>
</div>
"""
    write(OUT_DIR/"regions/index.html", render(tpl, cfg, f"지역별 | {cfg.get('site_name','')}", "지역별 목록", content))

    for r in region_list:
        lst = sorted(by[r], key=lambda x: x["name"])
        rows = "\n".join([f"<tr><td><a href='/p/{it['id']}/'>{it['name']}</a></td><td>{it.get('address','')}</td><td>{it.get('type','')}</td></tr>" for it in lst[:500]])
        page = f"""
<div class="card">
  <h1 class="h1">{r}</h1>
  <p class="notice">총 {len(lst)}개 (최대 500개 표시)</p>
  <table class="table">
    <thead><tr><th>이름</th><th>주소</th><th>유형</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>
"""
        write(OUT_DIR/f"regions/{slugify(r)}/index.html", render(tpl, cfg, f"{r} | {cfg.get('site_name','')}", f"{r} 공영주차장 목록", page))

def map_links(it):
    name = it.get("name","")
    addr = it.get("address","")
    # Search-based links are robust even if coords missing
    q = addr or name
    if not q:
        return ""
    return f"""
<div class="btnrow">
  <a class="btn" href="https://map.naver.com/v5/search/{q}" target="_blank" rel="noopener">네이버지도</a>
  <a class="btn" href="https://map.kakao.com/link/search/{q}" target="_blank" rel="noopener">카카오지도</a>
</div>
"""

def build_details(cfg, tpl, items):
    for it in items:
        content = f"""
<div class="card">
  <h1 class="h1">{it['name']}</h1>
  <div class="badge">{it['region']}</div>

  <div class="kv">
    <div>주소</div><div>{it.get('address','')}</div>
    <div>유형</div><div>{it.get('type','')}</div>
    <div>기관</div><div>{it.get('org','')}</div>
    <div>전화</div><div>{it.get('phone','')}</div>
    <div>좌표</div><div>{it.get('lat','')}, {it.get('lon','')}</div>
  </div>

  {map_links(it)}

  <div style="height:12px"></div>
  <div class="notice">
    ※ 요금/운영시간은 지자체별로 다를 수 있습니다. 지도/공식 안내를 반드시 확인하세요.
  </div>
</div>
"""
        title = f"{it['name']} | {cfg.get('site_name','')}"
        desc = f"{it['region']} {it.get('address','')} 공영주차장 정보"
        write(OUT_DIR/f"p/{it['id']}/index.html", render(tpl, cfg, title, desc, content))

def build_data(items):
    (OUT_DIR/"data").mkdir(parents=True, exist_ok=True)
    (OUT_DIR/"data/parking.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

def build_sitemap(cfg):
    base_url = (cfg.get("base_url") or "").rstrip("/")
    if not base_url:
        return
    urls = []
    for p in OUT_DIR.rglob("index.html"):
        rel = p.relative_to(OUT_DIR).as_posix()
        url = base_url + ("/" if rel=="index.html" else "/" + rel.replace("index.html",""))
        urls.append(url)
    lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml = ["<?xml version='1.0' encoding='UTF-8'?>",
           "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for u in sorted(set(urls)):
        xml += ["  <url>", f"    <loc>{u}</loc>", f"    <lastmod>{lastmod}</lastmod>", "  </url>"]
    xml.append("</urlset>")
    (OUT_DIR/"sitemap.xml").write_text("\n".join(xml), encoding="utf-8")
    (OUT_DIR/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8")

def clean_out():
    if OUT_DIR.exists():
        import shutil
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    cfg = read_config()
    tpl = read_template()
    csv_path = pick_csv_path()
    items = load_items(csv_path)

    clean_out()
    copy_assets()
    build_data(items)
    build_index(cfg, tpl, items)
    build_about(cfg, tpl, csv_path, items)
    build_regions(cfg, tpl, items)
    build_details(cfg, tpl, items)
    build_sitemap(cfg)

    (OUT_DIR/".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(items)} items from {csv_path}")

if __name__ == "__main__":
    main()
