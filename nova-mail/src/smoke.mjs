import { sendEmail } from './core.mjs';

const result=await sendEmail({
  provider:'gmail',
  to:'test@example.com',
  subject:'blocked',
  text:'blocked',
  approved:false
});

if(!result.blocked)throw new Error('Nova Mail approval gate failed');
console.log(JSON.stringify({ok:true,approvalGate:'enforced',reason:result.reason}));
