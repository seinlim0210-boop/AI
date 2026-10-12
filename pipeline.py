import os, json, csv, io, zipfile, re, time, sys
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import requests
ROOT=Path(__file__).resolve().parents[1]
def save(path,obj):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
class Dart:
 def __init__(self,key): self.key=key;self.session=requests.Session()
 def get(self,endpoint,**params):
  for attempt in range(3):
   try:
    r=self.session.get('https://opendart.fss.or.kr/api/'+endpoint,params={'crtfc_key':self.key,**params},timeout=90)
    if r.status_code==429 or r.status_code>=500:
     time.sleep(2**attempt);continue
    r.raise_for_status();time.sleep(.2);return r
   except requests.RequestException:
    if attempt==2: raise RuntimeError('DART 네트워크 요청 실패 (주소/키는 로그에서 숨김)') from None
    time.sleep(2**attempt)
  raise RuntimeError('DART HTTP 재시도 실패')
 def json(self,endpoint,**params):
  d=self.get(endpoint,**params).json()
  if d.get('status')=='013':return d
  if d.get('status')!='000':raise RuntimeError('DART '+str(d.get('status'))+': '+str(d.get('message')))
  return d
 def binary(self,endpoint,**params):
  b=self.get(endpoint,**params).content
  if not zipfile.is_zipfile(io.BytesIO(b)):
   try:
    e=ET.fromstring(b);msg=e.findtext('message') or 'ZIP 응답 아님';code=e.findtext('status')
   except ET.ParseError: msg='ZIP 응답 아님';code='unknown'
   raise RuntimeError('DART '+str(code)+': '+msg)
  return b
# 정확한 표준 ID 우선. 사용자 확장 계정은 계정명 완전일치만 사용하며 모호하면 결측.
MAP={
 'assets':('BS',['ifrs-full_Assets'],['자산총계','총자산']),
 'liabilities':('BS',['ifrs-full_Liabilities'],['부채총계']),
 'equity':('BS',['ifrs-full_Equity'],['자본총계']),
 'parent_equity':('BS',['ifrs-full_EquityAttributableToOwnersOfParent'],['지배기업의 소유주에게 귀속되는 자본','지배기업 소유주지분']),
 'cash':('BS',['ifrs-full_CashAndCashEquivalents'],['현금및현금성자산']),
 'current_assets':('BS',['ifrs-full_CurrentAssets'],['유동자산']),
 'current_liabilities':('BS',['ifrs-full_CurrentLiabilities'],['유동부채']),
 'inventory':('BS',['ifrs-full_Inventories'],['재고자산']),
 'receivables':('BS',[],['매출채권']),
 'payables':('BS',[],['매입채무']),
 'revenue':('IS',['ifrs-full_Revenue'],['매출액','영업수익','수익(매출액)']),
 'cost_of_sales':('IS',['ifrs-full_CostOfSales'],['매출원가']),
 'gross_profit':('IS',['ifrs-full_GrossProfit'],['매출총이익','매출총이익(손실)']),
 'operating_profit':('IS',['dart_OperatingIncomeLoss'],['영업이익','영업이익(손실)','영업손실']),
 'net_income':('IS',['ifrs-full_ProfitLoss'],['당기순이익','당기순이익(손실)','당기순손실']),
 'parent_income':('IS',['ifrs-full_ProfitLossAttributableToOwnersOfParent'],['지배기업 소유주지분 순이익','지배기업의 소유주에게 귀속되는 당기순이익(손실)']),
 'interest':('IS',['ifrs-full_InterestExpense'],['이자비용']),
 'cfo':('CF',['ifrs-full_CashFlowsFromUsedInOperatingActivities'],['영업활동현금흐름','영업활동으로 인한 현금흐름']),
 'cfi':('CF',['ifrs-full_CashFlowsFromUsedInInvestingActivities'],['투자활동현금흐름','투자활동으로 인한 현금흐름']),
 'cff':('CF',['ifrs-full_CashFlowsFromUsedInFinancingActivities'],['재무활동현금흐름','재무활동으로 인한 현금흐름']),
 'ppe_capex':('CF',['ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'],['유형자산의 취득','유형자산 취득']),
 'intangible_capex':('CF',['ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities'],['무형자산의 취득','무형자산 취득'])}
def norm(s):return re.sub(r'\s+','',s or '')
def amount(s):
 if s is None or str(s).strip() in ('','-'):return None
 s=str(s).replace(',','').strip();s='-'+s[1:-1] if s.startswith('(') and s.endswith(')') else s
 try:return int(s)
 except ValueError:return None

def extract(rows):
 values={};audit={}
 for key,(sj,ids,names) in MAP.items():
  pool=[r for r in rows if r.get('sj_div') in (['IS','CIS'] if sj=='IS' else [sj])]
  # IS 우선, CIS가 중복 존재할 때 같은 손익을 두 번 합산하지 않음
  if sj=='IS' and any(r.get('sj_div')=='IS' for r in pool):pool=[r for r in pool if r.get('sj_div')=='IS']
  hits=[r for r in pool if r.get('account_id') in ids]
  if not hits:hits=[r for r in pool if norm(r.get('account_nm')) in [norm(n) for n in names]]
  usable=[r for r in hits if r.get('currency') in (None,'','KRW')]
  r=usable[0] if len(usable)==1 else None
  values[key]=amount(r.get('thstrm_amount')) if r else None
  audit[key]={'status':'matched' if r else ('ambiguous' if hits else 'missing'),'row':r,'candidates':hits if not r else []}
 # CAPEX는 두 현금지출 항목이 모두 확인된 경우만 계산 (결측을 0으로 간주하지 않음)
 values['capex']=sum(abs(values[k]) for k in ('ppe_capex','intangible_capex')) if all(values[k] is not None for k in ('ppe_capex','intangible_capex')) else None
 values['fcf']=values['cfo']-values['capex'] if values['cfo'] is not None and values['capex'] is not None else None
 return values,audit

def div(a,b,scale=1):return a/b*scale if a is not None and b is not None and b>0 else None
def ratios(v,prev):
 def avg(k):return (v[k]+prev[k])/2 if prev and v.get(k) is not None and prev.get(k) is not None else None
 r={k:div(v.get(a),v.get(b),100) for k,a,b in [('gross_margin','gross_profit','revenue'),('operating_margin','operating_profit','revenue'),('net_margin','net_income','revenue'),('current_ratio','current_assets','current_liabilities'),('debt_ratio','liabilities','equity'),('equity_ratio','equity','assets')]}
 r['roa']=div(v.get('net_income'),avg('assets'),100)
 r['roe']=div(v.get('parent_income'),avg('parent_equity'),100)
 r['roe_total']=div(v.get('net_income'),avg('equity'),100)
 r['asset_turnover']=div(v.get('revenue'),avg('assets'))
 r['dso']=div(avg('receivables'),v.get('revenue'),365)
 r['dio']=div(avg('inventory'),v.get('cost_of_sales'),365)
 r['cfo_net_income']=div(v.get('cfo'),v.get('net_income'))
 r['interest_coverage']=div(v.get('operating_profit'),v.get('interest'))
 old=prev.get('revenue') if prev else None
 r['revenue_growth']=(v['revenue']/old-1)*100 if old is not None and old>0 and v.get('revenue') is not None else None
 return r

def main():
 cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8'));key=os.environ.get('DART_API_KEY','')
 if len(key)!=40:raise RuntimeError('40자리 DART_API_KEY를 GitHub Actions Secret 또는 환경변수로 설정하세요.')
 api=Dart(key);b=api.binary('corpCode.xml')
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  name=next(n for n in z.namelist() if n.upper().endswith('CORPCODE.XML'));tree=ET.fromstring(z.read(name))
 corps=[{c.tag:c.text for c in e} for e in tree.findall('list') if e.findtext('corp_name')==cfg['company']]
 if len(corps)!=1:raise RuntimeError('회사명 정확일치가 유일하지 않습니다. config.json을 확인하세요.')
 corp=corps[0];code=corp['corp_code'];records=[];baseline=None;warnings=[]
 for year in range(cfg['start_year']-1,cfg['end_year']+1):
  d=api.json('fnlttSinglAcntAll.json',corp_code=code,bsns_year=year,reprt_code='11011',fs_div=cfg['fs_div'])
  save(f'data/raw/{year}_{cfg["fs_div"]}.json',d)
  if d.get('status')=='013':warnings.append(f'{year}: 연간 {cfg["fs_div"]} 자료 없음');baseline=None;continue
  values,audit=extract(d['list']);r=ratios(values,baseline)
  save(f'data/audit/{year}.json',audit)
  if year>=cfg['start_year']:
   receipts=sorted(set(x['rcept_no'] for x in d['list'] if x.get('rcept_no')))
   records.append({'year':year,'fs_div':cfg['fs_div'],'values':values,'ratios':r,'receipt_numbers':receipts,'missing':[k for k,a in audit.items() if a['status']!='matched']})
  baseline=values
 reports=[];page=1
 while True:
  d=api.json('list.json',corp_code=code,bgn_de=cfg['reports_since'],end_de=datetime.now().strftime('%Y%m%d'),pblntf_ty='A',last_reprt_at='Y',page_count=100,page_no=page)
  if d.get('status')=='013':break
  reports.extend(d.get('list',[]))
  if page>=int(d['total_page']):break
  page+=1
 for r in reports:
  receipt=r['rcept_no'];p=ROOT/f'data/reports/{receipt}.zip';p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():p.write_bytes(api.binary('document.xml',rcept_no=receipt))
 # 재무 API의 접수번호도 원문 보관: 검색 최종본과 다른 정정 이력 추적 가능
 for receipt in sorted({n for r in records for n in r['receipt_numbers']}):
  p=ROOT/f'data/reports/{receipt}.zip'
  if not p.exists():p.write_bytes(api.binary('document.xml',rcept_no=receipt))
 payload={'company':corp,'generated_at':datetime.now(timezone.utc).isoformat(),'config':cfg,'records':records,'reports':reports,'warnings':warnings}
 save('docs/data/financials.json',payload);save('data/reports/index.json',reports)
 for kind in ('values','ratios'):
  p=ROOT/f'docs/data/{kind}.csv';keys=sorted({k for r in records for k in r[kind]})
  with p.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['year','fs_div']+keys);w.writeheader()
   for row in records:w.writerow({'year':row['year'],'fs_div':row['fs_div'],**row[kind]})
 text=['# 알테오젠 연간 재무분석','',f'기준: {cfg["fs_div"]} / 금액 원 / 비율 %','']
 for row in records:
  v=row['values'];rr=row['ratios'];text.extend([f'## {row["year"]}',f'- 매출액: {v["revenue"]}; 영업이익: {v["operating_profit"]}; CFO: {v["cfo"]}; FCF: {v["fcf"]}',f'- 매출증가율: {rr["revenue_growth"]}; 영업이익률: {rr["operating_margin"]}; ROA: {rr["roa"]}; 지배주주 ROE: {rr["roe"]}',f'- 자동 매칭 결측/모호 항목: {", ".join(row["missing"])}'])
  if v['net_income'] is not None and v['cfo'] is not None and v['net_income']>0 and v['cfo']<v['net_income']:text.append('- 확인 필요: CFO가 순이익보다 작습니다. 운전자본 및 비현금손익을 확인하세요.')
  if v['fcf'] is not None and v['fcf']<0:text.append('- 확인 필요: FCF 음수. 성장투자와 유지투자, 외부조달 의존도를 확인하세요.')
 (ROOT/'docs/analysis.md').write_text('\n'.join(text),encoding='utf-8')
 if not records:raise RuntimeError('분석 가능한 연간 재무자료가 없습니다. 설정을 확인하세요.')
 print(f'완료: {len(records)}개 연도, {len(reports)}개 정기공시. 결측은 audit에서 검토하세요.')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
