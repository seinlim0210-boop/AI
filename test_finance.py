import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pipeline import ratios, extract, amount, MAP
class FinanceTests(unittest.TestCase):
 def test_ratios(self):
  v={k:None for k in MAP};v.update(revenue=200,operating_profit=20,net_income=10,assets=120,equity=60,liabilities=60,parent_income=8,parent_equity=40,cfo=15,current_assets=50,current_liabilities=25,inventory=10,receivables=20,cost_of_sales=100,interest=2)
  p=v.copy();p.update(revenue=100,assets=80,equity=40,parent_equity=24,receivables=10,inventory=6)
  r=ratios(v,p)
  self.assertEqual(r['revenue_growth'],100);self.assertEqual(r['operating_margin'],10);self.assertEqual(r['roa'],10);self.assertEqual(r['roe'],25);self.assertEqual(r['roe_total'],20);self.assertEqual(r['dso'],27.375);self.assertEqual(r['current_ratio'],200)
  self.assertIsNone(ratios(v,None)['roa'])
 def test_missing_and_ambiguity(self):
  row={'sj_div':'BS','account_id':'ifrs-full_Assets','account_nm':'자산총계','thstrm_amount':'1,000','currency':'KRW'}
  v,a=extract([row]);self.assertEqual(v['assets'],1000);self.assertIsNone(v['capex']);self.assertIsNone(v['fcf'])
  v,a=extract([row,row]);self.assertIsNone(v['assets']);self.assertEqual(a['assets']['status'],'ambiguous')
 def test_negative_denominator(self):
  v={k:None for k in MAP};v.update(revenue=0,equity=-1,liabilities=1,net_income=-5,cfo=1)
  r=ratios(v,v);self.assertIsNone(r['debt_ratio']);self.assertIsNone(r['cfo_net_income']);self.assertIsNone(r['revenue_growth'])
 def test_capex(self):
  rows=[{'sj_div':'CF','account_id':MAP[k][1][0],'thstrm_amount':str(v),'currency':'KRW'} for k,v in [('cfo',100),('ppe_capex',-20),('intangible_capex',5)]]
  v,_=extract(rows);self.assertEqual(v['capex'],25);self.assertEqual(v['fcf'],75)
 def test_parse(self):self.assertEqual(amount('(1,234)'),-1234);self.assertIsNone(amount('-'))
if __name__=='__main__':unittest.main()
