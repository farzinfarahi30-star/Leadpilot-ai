import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true});
try{
  const page=await browser.newPage();
  await page.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000});
  console.log(JSON.stringify({ok:true,title:await page.title(),url:page.url()}));
}finally{await browser.close()}
