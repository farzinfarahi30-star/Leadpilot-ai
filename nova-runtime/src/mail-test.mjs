import { runAgentCycle } from './agent-runtime.mjs';

if(!process.env.NOVA_MAIL_TEST_TO) throw new Error('NOVA_MAIL_TEST_TO secret is required');
if(process.env.NOVA_MAIL_TEST_APPROVED!=='true') throw new Error('NOVA_MAIL_TEST_APPROVED must be true for this explicit test');

const result=await runAgentCycle(1);
const sales=result.agents.find(function(agent){return agent.agent==='sales-expert';});
console.log(JSON.stringify({runtime:result.runtime,cycle:result.cycle,sales:sales},null,2));

if(!sales||sales.status!=='completed'||!sales.email||sales.email.sent!==true) process.exitCode=1;
