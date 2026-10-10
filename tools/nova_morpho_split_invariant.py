#!/usr/bin/env python3
"""Offline Twyne Morpho liquidation arithmetic property screening.

Source: 0xTwyne/twyne-contracts-v1:
  src/twyne/MorphoCollateralVault.sol, splitCollateralAfterExtLiq
  src/twyne/CollateralVaultBase.sol, collateralForBorrower

CAUTION: Simplified mathematical model, not a Solidity runtime / fork / PoC.
Does NOT access blockchain, private keys, or live systems.
"""
import random

FACTOR = 10_000
SCALE = 10**36

def borrower_claim(b, c, cap, price, buffer=9700, ext_lltv=8600, max_lltv=9000):
    adjusted = buffer * ext_lltv
    def convert(v):
        return min(cap, v * SCALE // price)
    if FACTOR * b >= max_lltv * c:
        return 0
    if 10**8 * b <= adjusted * c:
        return convert(c - b)
    v = (10**8-adjusted)*(max_lltv*c-FACTOR*b)//(FACTOR*(FACTOR*max_lltv-adjusted))
    return convert(v)

def split(actual, debt, release_max, price, total):
    if debt == 0:
        release = min(actual, release_max)
        return 0, release, actual-release
    owned_min = (debt*FACTOR//9000)*SCALE//price
    user_min = min(actual, owned_min)
    release = min(actual-user_min, release_max)
    collateral = actual-release
    claim = borrower_claim(debt, collateral*price//SCALE, total-release_max, price)
    return (collateral-claim)%(2**256), release, claim

def main():
    rng = random.Random(20261010)
    for i in range(200_000):
        total = rng.randrange(100_000,10**15)
        actual = rng.randrange(1,total)
        release_max = rng.randrange(0,total)
        price = rng.choice([10**35, 10**36, 2*10**36, 5*10**36, 100*10**36])
        debt = rng.randrange(0,max(1,(actual*price//SCALE*8)//10+1))
        liquidator,lp,borrower = split(actual,debt,release_max,price,total)
        assert liquidator + lp + borrower == actual, (i,actual,debt,release_max,price,total,liquidator,lp,borrower)
        assert max(liquidator,lp,borrower)<=actual
    print("PASS 200000 seeded local conservation checks; NO verified reward-eligible finding")

if __name__=="__main__":
    main()
