# 전국 공영주차장 찾기 (정적 사이트 + GitHub Pages 자동배포)

코딩 없이 “업로드/클릭”만으로 배포하는 미니 웹서비스 템플릿입니다.

- 공공데이터포털 안내에 따르면, 이 데이터는 **파일데이터를 로그인 없이 다운로드**해서 이용할 수 있습니다.
- 또한 데이터 상세 페이지에 **이용허락범위: 제한 없음**으로 표시된 것을 확인하고 사용하세요.

> ⚠️ 이 레포에는 시연용 `data/parking_sample.csv`만 들어 있습니다.  
> 전국 실데이터를 쓰려면 아래 “실데이터로 교체”만 1번 해주세요. (코딩 X)

---

## 1) 배포(자동) — GitHub Pages

### A. 레포 만들기
1. GitHub에서 새 Repository 생성 (Public 권장)
2. 이 폴더의 파일 전체를 **Upload files**로 업로드 (드래그&드롭 가능)

### B. Pages 켜기 (클릭 몇 번)
1. GitHub 레포 → **Settings**
2. 좌측 **Pages**
3. **Build and deployment** → Source를 **GitHub Actions**로 선택

첫 푸시 후 Actions가 완료되면 Pages 주소가 생깁니다.

---

## 2) 실데이터로 교체(추천, 1회)

1. 공공데이터포털에서 아래 데이터로 이동해 CSV를 다운로드하세요.  
   - “한국교통안전공단_전국공영주차장정보” (파일데이터)

2. 다운로드한 CSV 파일을 레포에 업로드:
   - 레포의 `data/source.csv` 로 업로드 (파일명 정확히)
   - GitHub 웹에서 **Add file → Upload files** 사용

3. 업로드(커밋)하면 자동으로 다시 빌드/배포됩니다.

> 이후 데이터가 갱신되면 같은 방식으로 `data/source.csv`만 새로 올리면 됩니다.

---

## 3) 광고(AdSense) 붙이기

승인 후, `site_template/config.json`의 `adsense_client` / `adsense_slot_*`를 채워 넣으면
템플릿에 광고 영역이 노출됩니다.

---

## 4) 빌드/구조

- `scripts/build.py`: CSV(실데이터 or 샘플) → `site/` 정적 HTML 생성
- `site/`: GitHub Pages에 배포되는 결과물
- `site_template/`: 공통 HTML 템플릿/스타일/설정

