#!/usr/bin/env python3
"""Exact modular obstruction search. No third-party dependencies.

If an integer polynomial equation f(x_1,...,x_n)=0 has no solution
modulo m, it has no integer solution. Non-obstruction is INCONCLUSIVE.
This is established number theory, not a new theorem.
"""
import ast
import itertools
import json
import argparse

class Unsupported(ValueError): pass

def expr(node, env, mod):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value % mod
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -expr(node.operand, env, mod) % mod
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add): return (expr(node.left,env,mod)+expr(node.right,env,mod))%mod
        if isinstance(node.op, ast.Sub): return (expr(node.left,env,mod)-expr(node.right,env,mod))%mod
        if isinstance(node.op, ast.Mult): return (expr(node.left,env,mod)*expr(node.right,env,mod))%mod
        if isinstance(node.op, ast.Pow):
            if not isinstance(node.right, ast.Constant) or type(node.right.value) is not int or not 0<=node.right.value<=32:
                raise Unsupported('Exponent must be integer in [0,32]')
            return pow(expr(node.left,env,mod),node.right.value,mod)
    raise Unsupported('Only integer-polynomial expressions are allowed')

def parse(s):
    if len(s)>600: raise Unsupported('Expression too long')
    tree=ast.parse(s,mode='eval')
    if sum(1 for _ in ast.walk(tree))>220: raise Unsupported('Expression too complex')
    names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name)})
    if not names or len(names)>3 or any(len(n)>12 or not n.isidentifier() for n in names):
        raise Unsupported('Must use 1 to 3 named integer variables')
    expr(tree.body,{n:0 for n in names},2)  # validate all syntax
    return tree.body,names

def certify(equation, moduli=(2,3,4,5,7,8,9,11,13,16), max_cases=25000):
    if '=' not in equation: raise Unsupported('Equation must contain one =')
    a,b=equation.split('=',1)
    tree,names=parse(f'({a})-({b})')
    for m in moduli:
        if m<2 or m**len(names)>max_cases: continue
        count=0
        hit=False
        for residues in itertools.product(range(m),repeat=len(names)):
            count+=1
            if expr(tree,dict(zip(names,residues)),m)==0:
                hit=True
                break
        if not hit:
            return {'status':'PROVED_NO_INTEGER_SOLUTION','equation':equation,
                    'variables':names,'modulus':m,'residue_cases':count,
                    'reason':'Every integer tuple reduces modulo m, and all residues fail the equation.'}
    return {'status':'INCONCLUSIVE','equation':equation,'variables':names,
            'reason':'No modular obstruction within configured search range; an integer solution is not implied.'}

def verify_certificate(c):
    if c.get('status')!='PROVED_NO_INTEGER_SOLUTION': return False
    m=c.get('modulus')
    if type(m) is not int or m<2 or m>64:return False
    a,b=c['equation'].split('=',1)
    tree,names=parse(f'({a})-({b})')
    if names!=c.get('variables') or m**len(names)>25000:return False
    if c.get('residue_cases')!=m**len(names):return False
    return all(expr(tree,dict(zip(names,residues)),m)!=0
               for residues in itertools.product(range(m),repeat=len(names)))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('equation')
    a=p.parse_args()
    result=certify(a.equation)
    result['independently_rechecked']=verify_certificate(result)
    print(json.dumps(result,indent=2))
