/* Export the editable source with the official draw.io renderer, entirely offline.
 * Authoring only: npm install playwright; npx playwright install chromium
 * Run: node scripts/round3/visuals/export_drawio.cjs
 * Set DRAWIO_WEBAPP_DIR to an extracted official draw.war (tested: draw.io v32.6.10).
 * Obtain the package from https://github.com/jgraph/drawio/releases; unzip as a ZIP.
 * The renderer is served on loopback; Chromium blocks all non-loopback requests.
 * Optional: PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH points to an existing Chromium.
 * Protocol: https://www.drawio.com/docs/reference/embed-mode/#export
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require('playwright');

async function main() {
  const dir = path.resolve(__dirname, '../../../docs/round3/assets');
  if(!process.env.DRAWIO_WEBAPP_DIR)throw new Error('Set DRAWIO_WEBAPP_DIR to an extracted official draw.war directory.');
  const webapp = path.resolve(process.env.DRAWIO_WEBAPP_DIR);
  const xml = fs.readFileSync(path.join(dir, 'architecture-before-after.drawio'), 'utf8');
  const server = http.createServer((req, res) => {
    const requestPath = new URL(req.url, 'http://127.0.0.1').pathname;
    if(requestPath.startsWith('/drawio/')) {
      const localPath = path.resolve(webapp, '.' + decodeURIComponent(requestPath.slice('/drawio'.length)));
      if(localPath!==webapp&&!localPath.startsWith(webapp+path.sep)){res.writeHead(403);res.end();return;}
      const filename = fs.existsSync(localPath) && fs.statSync(localPath).isDirectory()?path.join(localPath,'index.html'):localPath;
      if(!fs.existsSync(filename)){res.writeHead(404);res.end();return;}
      const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.gif':'image/gif','.xml':'application/xml','.txt':'text/plain','.json':'application/json'}[path.extname(filename)]||'application/octet-stream';
      res.writeHead(200,{'Content-Type':mime});fs.createReadStream(filename).pipe(res);return;
    }
    res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
    res.end(`<!doctype html><meta charset="utf-8"><title>OneOrder draw.io export</title>
      <script>window.events=[];window.result=null;
      window.addEventListener('message', e => {
        if(e.origin!==window.location.origin)return;
        let m;try{m=JSON.parse(e.data)}catch{return}
        window.events.push({event:m.event,error:m.error});
        const send=x=>e.source.postMessage(JSON.stringify(x),e.origin);
        if(m.event==='init')send({action:'load',xml:${JSON.stringify(xml)},background:'#FFFFFF'});
        if(m.event==='load')send({action:'export',format:'xmlpng',width:1920,size:'page',border:0,background:'#FFFFFF',transparent:false});
        if(m.event==='export')window.result=m;
      });</script>
      <iframe src="/drawio/?embed=1&proto=json&spin=1&ui=min&noSaveBtn=1&noExitBtn=1&offline=1&local=1" style="width:100%;height:100vh;border:0"></iframe>`);
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  let browser;
  try {
    browser = await chromium.launch({headless:true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH}: {})});
    const page = await browser.newPage({viewport:{width:1920,height:1080}});
    page.on('pageerror', error => console.error('Renderer:', error.message));
    page.on('console', message => {if(message.type()==='error')console.error('Renderer:',message.text());});
    await page.route('**/*', route => {
      const url=route.request().url();
      if(url.startsWith('http://127.0.0.1:')||url.startsWith('data:')||url.startsWith('blob:'))return route.continue();
      return route.abort();
    });
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    try {
      await page.waitForFunction(() => window.result !== null, null, {timeout:60000});
    } catch (err) {
      console.error('draw.io events:', await page.evaluate(() => window.events));
      console.error('Frames:', await Promise.all(page.frames().map(async f=>({url:f.url(),text:(await f.locator('body').innerText()).slice(0,500)}))));
      throw err;
    }
    const result = await page.evaluate(() => window.result);
    if(result.error) throw new Error(result.error);
    if(!result.data?.startsWith('data:image/png;base64,'))throw new Error('No PNG returned by draw.io');
    fs.writeFileSync(path.join(dir, 'architecture-before-after.png'),Buffer.from(result.data.split(',')[1],'base64'));
    console.log('Exported architecture-before-after.png using offline draw.io renderer.');
  } finally {
    if(browser) await browser.close();
    server.close();
  }
}
main().catch(err=>{console.error(err);process.exitCode=1;});
