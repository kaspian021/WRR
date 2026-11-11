import unittest
from exercise5_wrr import Task,schedule
class Tests(unittest.TestCase):
 def test_weight_order(self):
  r=schedule([Task("A",2,5),Task("B",1,4)])
  self.assertEqual([e["task"] for e in r["events"][:3]],["A","A","B"])
 def test_modes_match(self):
  rs=[schedule([Task("A",3,5),Task("B",1,4)],mode=m) for m in ("semaphore","monitor","both")]
  self.assertEqual(rs[0]["gantt"],rs[1]["gantt"]); self.assertEqual(rs[1]["gantt"],rs[2]["gantt"])
 def test_metrics(self):
  r=schedule([Task("A",1,3),Task("B",1,2)])
  self.assertEqual(r["makespan"],5); self.assertEqual(r["metrics"]["A"]["completion"],5); self.assertEqual(r["metrics"]["B"]["completion"],4)
 def test_final_slice(self):
  self.assertEqual([e["duration"] for e in schedule([Task("A",2,3)],2)["events"]],[2,1])
 def test_zero_burst(self): self.assertEqual(schedule([Task("A",1,0)])["makespan"],0)
 def test_bad_quantum(self):
  with self.assertRaises(ValueError): schedule([Task("A",1,1)],0)
 def test_bad_weight(self):
  with self.assertRaises(ValueError): Task("A",0,1)
 def test_duplicate(self):
  with self.assertRaises(ValueError): schedule([Task("A",1,1),Task("A",2,1)])
 def test_bad_mode(self):
  with self.assertRaises(ValueError): schedule([Task("A",1,1)],mode="x")
if __name__=="__main__": unittest.main()
