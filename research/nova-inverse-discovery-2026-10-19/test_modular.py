import unittest,random
from modular_obstruction import certify,verify_certificate,Unsupported
class Tests(unittest.TestCase):
 def test_known_obstruction(self):
  for equation in ['x**2+y**2=3','x**2=3','x**2+y**2=7','x**2=2']:
   c=certify(equation)
   self.assertEqual(c['status'],'PROVED_NO_INTEGER_SOLUTION',c)
   self.assertTrue(verify_certificate(c))
 def test_inconclusive_with_solution(self):
  for equation in ['x**2+y**2=5','x**2=4','x+y=3']:
   self.assertEqual(certify(equation)['status'],'INCONCLUSIVE')
 def test_tamper(self):
  c=certify('x**2+y**2=3')
  for key,value in [('modulus',2),('residue_cases',2),('variables',['z','y']),('equation','x+y=3')]:
   bad=dict(c);bad[key]=value
   self.assertFalse(verify_certificate(bad),(key,bad))
 def test_no_code_execution(self):
  for s in ['__import__("os").system("echo hacked")=0','x/2=1','x**100=0']:
   with self.assertRaises((Unsupported,ValueError,SyntaxError)):certify(s)
 def test_random_obstructions_sound(self):
  r=random.Random(20261019)
  for _ in range(1000):
   a,b,c=[r.randint(-12,12) for j in range(3)]
   equation=f'{a}*x**2+{b}*y**2={c}'
   cert=certify(equation,moduli=(2,3,4,5,7,8,9,11))
   if cert['status']=='PROVED_NO_INTEGER_SOLUTION':
    self.assertTrue(verify_certificate(cert))
    # independently brute-check bounded integer tuples to test for false positives
    self.assertFalse(any(a*x*x+b*y*y==c for x in range(-15,16) for y in range(-15,16)),equation)
if __name__=='__main__':unittest.main(verbosity=2)
