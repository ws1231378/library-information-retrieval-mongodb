const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
const root=path.resolve(__dirname,'..'),out=path.join(root,'results','screenshots');fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1});
for(let i=0;i<36;i++){await page.goto('http://127.0.0.1:28780/?page='+i);await page.locator('h2').waitFor();await page.screenshot({path:path.join(out,String(i+1).padStart(2,'0')+'.png'),fullPage:true});}
await page.goto('http://127.0.0.1:28780/?page=11');
const downloadPromise=page.waitForEvent('download');await page.getByRole('link',{name:'导出分类统计 JSON'}).click();const download=await downloadPromise;await download.saveAs(path.join(root,'results','graphical_export.json'));
fs.writeFileSync(path.join(root,'results','browser_verification.json'),JSON.stringify({client:'Local read-only verification web client',screenshots:36,export:'graphical_export.json',capturedAt:new Date().toISOString()},null,2));
await browser.close();console.log('36 actual browser screenshots and graphical export saved');
})();

