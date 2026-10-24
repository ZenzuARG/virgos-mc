'use strict';
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {Controller}=require('./core.cjs');
function createServer(controller, options={}) {
  const token=crypto.randomBytes(32).toString('hex');
  const server=http.createServer(async(req,res)=>{
    const port=server.address().port, expected=`127.0.0.1:${port}`;
    const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"};
    const send=(status,data,type='application/json; charset=utf-8')=>{res.writeHead(status,{...headers,'Content-Type':type});res.end(type.startsWith('application/json')?JSON.stringify(data):data);};
    if(req.headers.host!==expected||req.headers.origin&&req.headers.origin!==`http://${expected}`||req.headers['sec-fetch-site']==='cross-site') return send(403,{error:'Este panel sólo admite acceso desde esta PC y su propia página.'});
    const url=new URL(req.url,`http://${expected}`);
    if(req.method==='GET'&&url.pathname==='/health') return send(200,{app:'virgos-admin',version:1,root:controller.root});
    if(req.method==='GET'&&['/','/app.js','/style.css','/icon.svg'].includes(url.pathname)) {
      const name=url.pathname==='/'?'index.html':url.pathname.slice(1), types={'index.html':'text/html; charset=utf-8','app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8','icon.svg':'image/svg+xml'};
      return send(200,fs.readFileSync(path.join(__dirname,'web',name),'utf8').replaceAll('__CSRF__',token),types[name]);
    }
    if(req.headers['x-panel-token']!==token) return send(403,{error:'Sesión vencida. Recargá la página del panel.'});
    try {
      if(req.method==='GET'&&url.pathname==='/api/status') {const s=await controller.status();return send(200,{...s,players:controller.players(s),permissions:controller.permissions()});}
      if(req.method==='GET'&&url.pathname==='/api/logs') return send(200,controller.logs());
      if(req.method==='POST'&&url.pathname==='/api/action') {
        if(req.headers.origin!==`http://${expected}`||!/^application\/json(?:;|$)/i.test(req.headers['content-type']||'')) return send(403,{error:'Solicitud no admitida.'});
        let data='',size=0; for await(const chunk of req) {size+=chunk.length;if(size>8192)return send(413,{error:'Solicitud demasiado grande.'}); data+=chunk;}
        let body;try {body=JSON.parse(data);}catch{return send(400,{error:'JSON inválido.'});}
        if(!body||typeof body!=='object'||Array.isArray(body))return send(400,{error:'Solicitud inválida.'});
        return send(200,await controller.action(body));
      }
      send(404,{error:'Ruta no encontrada.'});
    } catch(error) {send(400,{error:error.message});}
  });
  server.requestTimeout=15000;server.headersTimeout=10000;
  return server;
}
if(require.main===module) {
  const root=path.resolve(__dirname,'../..'),server=createServer(new Controller(root));
  server.on('error',error=>{console.error(error.code==='EADDRINUSE'?'El puerto 8765 ya está en uso.':error.message);process.exitCode=1;});
  server.listen(8765,'127.0.0.1',()=>{fs.writeFileSync(path.join(root,'.runtime/admin-panel.json'),JSON.stringify({pid:process.pid,url:'http://127.0.0.1:8765',started:new Date().toISOString()}));console.log('Virgos-MC · Panel local en http://127.0.0.1:8765');});
}
module.exports={createServer};
