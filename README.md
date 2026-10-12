# 알테오젠 DART 보고서 아카이브 · 재무분석 대시보드
대상 저장소: https://github.com/seinlim0210-boop/AI.git

## 현재 상태 — 꼭 확인하세요
이 ZIP은 실행 가능한 수집/분석/배포 프로젝트입니다. API 키와 저장소 쓰기 권한이 제공되지 않아 **실제 DART 재무수치, 기업보고서 ZIP 및 GitHub 업로드는 아직 수행하지 않았습니다.** docs/data/financials.json은 결측 안내만 포함합니다. 예시/가짜 기업 수치는 없습니다. 첨부 DOCX는 실적 데이터가 아닌 지표 정의 가이드이므로 계산 기준에 반영했습니다.

## 가장 쉬운 설치 (GitHub 웹 화면)
1. ZIP을 해제하고 파일을 AI 저장소 루트에 올립니다. `.github/workflows/update.yml` 등 숨김 폴더도 반드시 포함하세요. 기존 파일과 이름이 겹치면 덮어쓰기 전에 백업하세요. 워크플로 파일은 GitHub 편집기에서 `.github/workflows/update.yml` 경로로 생성할 수도 있습니다.
2. 저장소 Settings → Secrets and variables → Actions → New repository secret에서 이름 `DART_API_KEY`, 값에는 발급받은 40자리 키를 넣습니다. 키는 소스/HTML/커밋에 넣지 마세요.
3. Settings → Actions → General에서 Workflow permissions를 Read and write permissions로 설정합니다. 조직 정책이 제한하면 관리자 승인이 필요합니다.
4. Settings → Pages → Build and deployment → Source를 **GitHub Actions**로 설정합니다. 저장소 요금제/공개 여부에 따라 Pages 사용 가능 여부를 확인하세요.
5. Actions → DART collect and deploy → Run workflow를 실행합니다. 성공 후 워크플로가 실제 배포 URL을 표시합니다. 예상 URL은 https://seinlim0210-boop.github.io/AI/ 입니다(아직 배포된 주소라고 보장하지 않음).
6. `data/reports/`의 보고서 ZIP, `data/raw/`의 원 API 응답, `data/audit/`의 매칭 근거, `docs/data/`의 JSON/CSV를 확인하세요.

## Git으로 올리기
기존 저장소를 먼저 clone합니다. ZIP 해제 폴더의 **내용**을 clone 폴더 루트로 복사합니다(프로젝트 폴더 자체를 하위 폴더로 넣지 마세요).
```bash
git clone https://github.com/seinlim0210-boop/AI.git
cd AI
# ZIP 해제 파일들을 이 폴더에 복사한 후
git add .
git commit -m "Add Alteogen DART financial dashboard"
git push
```
계정 인증은 사용자 PC의 GitHub 인증 절차로 처리하세요. 토큰을 이 프로젝트에 기록하지 마세요.

## 수집 범위
- 기본: 2020~2025 **사업보고서 연간 연결(CFS)**. 평균잔액 계산을 위해 2019도 조회하되 대시보드에는 표시하지 않습니다.
- config.json에서 시작/종료 연도와 fs_div를 수정할 수 있습니다. OFS로 바꾸면 별도만 분석합니다. 연결 자료가 없다고 별도로 자동 대체하지 않습니다.
- 정기공시 원문: reports_since(기본 2020-01-01)부터 실행일까지 사업·반기·분기 보고서를 최종본 검색하여 보관합니다. 원문 ZIP은 DART 제공 XML 묶음이며 PDF가 아닙니다. 이전 실행에서 받은 정정 전 ZIP은 남아 이력으로 보관됩니다.
- 재무 API 접수번호의 원문도 별도로 보관합니다. 공시검색 최종본과 재무 API 정정 반영 시점이 다를 수 있으므로 receipt_numbers와 reports/index를 대조하세요.
- 2026 중간 실적은 원문만 수집합니다. 연간 비교에 분기/누적 실적을 섞지 않습니다. 2026 연간 공시 후 end_year를 2026으로 수정하세요.
- 매주 월요일 한국시간 07:20 자동 실행 및 수동 실행. 예약 실행은 기본 브랜치에서 작동하며 GitHub 정책에 따라 비활성화될 수 있습니다.

## 지표 정의 / 결측 정책
금액 저장 단위 원(KRW), 화면 단위 억원. API currency가 비KRW이면 자동 계산하지 않습니다.
- 매출총이익률, 영업이익률, 순이익률 = 해당 이익 / 매출 ×100.
- 매출증가율 = 당기 매출 / 전기 매출 −1. 전기 매출 0 이하 또는 누락 시 결측.
- ROA = 총순이익 / 평균 총자산. 지배주주 ROE = 지배순이익 / 평균 지배자본. 총자본 ROE도 별도 표시.
- 유동비율 = 유동자산 / 유동부채, 부채비율 = 총부채 / 총자본, 자기자본비율 = 총자본 / 총자산.
- 총자산회전율 = 매출 / 평균자산. DSO = 평균 매출채권 / 매출 ×365(전체 매출 대용, 외상매출과 다를 수 있음). DIO = 평균재고 / 매출원가 ×365.
- CFO/순이익, 영업이익/이자비용. 분모 0 이하이면 결측. 음수 영업이익과 양수 이자비용의 배율은 음수로 표시.
- CAPEX = 유형자산 취득 + 무형자산 취득 현금지출의 절댓값 합. 두 항목 모두 확인되어야 계산. FCF = CFO − CAPEX.
- 평균은 전년과 당년 기말의 단순평균. 전년 데이터가 없으면 평균 기반 비율 미산출. 각 연도 공시의 당기 수치를 이용하므로 후속 공시의 비교수치 재작성은 자동 소급 적용하지 않습니다.
- 표준 XBRL ID → 계정명 완전일치 순으로 매칭. 중복/모호한 계정은 합산하지 않고 null. 회사 확장 계정명은 audit를 확인한 뒤 scripts/pipeline.py의 MAP에 추가할 수 있습니다. 결측과 공시상 0은 다릅니다.

### 가이드에 있지만 자동 계산하지 않는 항목
당좌자산 구성, 이자부차입금(리스/전환사채 범위와 중복), 순차입금, EBITDA(상각비 중복), 순차입금/EBITDA, ROIC(NOPAT/투하자본/세율), WACC, DPO(외상매입액), CCC, EPS/BPS, PER/PBR, EV/EBITDA, FCF수익률은 추가 주석/시장데이터가 필요합니다. 없는 입력을 0이나 추정치로 대체하지 않습니다. finance-guide.md에 검토 항목을 정리했습니다.

알테오젠의 기술이전 계약금·마일스톤·로열티 및 연구개발비는 기간별 변동이 클 수 있습니다. 단순 비율만으로 반복 수익성과 기업가치를 단정하지 말고 원문 주석을 확인하세요. 본 프로젝트는 투자 권유가 아닙니다.

## 로컬 실행 (선택)
Python 3.10+가 필요합니다. DART_API_KEY를 사용자 환경변수로 설정한 후:
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/pipeline.py
```
`.env` 파일을 자동으로 읽지는 않습니다. 수집 후 docs를 정적 호스팅하거나 Pages에서 확인하세요. HTML을 더블클릭하면 브라우저 fetch 제한으로 JSON을 읽지 못할 수 있습니다. 화면은 Chart.js CDN 네트워크 연결이 필요하며 연결 실패해도 상세표는 표시됩니다.

## 오류 해결
010/011/901: API 키 상태 확인. 012: DART IP 제한 확인(GitHub 실행 IP가 달라질 수 있음). 013: 해당 연도/연결 자료 없음. 020: 요청 한도 초과, 다음 날 재실행. 800: 점검 후 재실행. Git push 실패: 쓰기 권한/브랜치 보호 정책 확인. Pages 실패: Source GitHub Actions와 요금제 확인. 결측 다수: data/audit의 계정명 확인.

원문이 커져 GitHub 파일 크기 제한/저장소 용량에 도달하면 별도 아카이브 전략을 적용해야 합니다. 첫 설치 및 수집은 여기서 실제 API 인증이나 브라우저 실행으로 검증하지 않았으며, 계산 로직과 정적 코드를 테스트했습니다.

## 공식 문서
- https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019018 (고유번호)
- https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001 (공시검색)
- https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003 (공시 원문 ZIP)
- https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020 (전체 재무제표)
