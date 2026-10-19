// Independent brute-force verifier of the n=10 qtBench #30 target distribution.
// Enumerates ALL 10! = 3,628,800 inversion sequences, no dynamic-programming recurrence.
#include <array>
#include <iostream>
#include <map>
using namespace std;
int main(){
 constexpr int n=10;
 array<int,n> e{};
 map<int,long long> fibers;
 long long visited=0,accepted=0;
 auto rec = [&](auto&& self,int i)->void{
   if(i==n){
     ++visited;
     if(e[n-1]==e[n-2])return;
     // No value may occur twice at non-consecutive positions.
     for(int a=0;a<n;a++)for(int b=a+2;b<n;b++)if(e[a]==e[b])return;
     bool used[n]={};int distinct=0;
     for(int v:e)if(!used[v]){used[v]=true;++distinct;}
     ++fibers[distinct]; ++accepted;
     return;
   }
   for(int v=0;v<=i;v++){e[i]=v;self(self,i+1);}
 };
 rec(rec,0);
 if(visited!=3628800||accepted!=16507||fibers!=map<int,long long>{{6,1800},{7,8400},{8,5796},{9,510},{10,1}}){
   cerr<<"FAIL: unexpected target count\n";return 1;
 }
 cout<<"PASS: "<<visited<<" unrestricted inversion sequences inspected; "<<accepted<<" valid minus-class sequences at n=10.\n";
 for(auto [d,c]:fibers)cout<<"grade="<<d<<" count="<<c<<"\n";
}