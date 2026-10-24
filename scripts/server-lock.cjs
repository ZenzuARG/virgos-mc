'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
// Shared with server-lock.ps1. Exclusive creation prevents simultaneous starts/backups.
function acquire(root,kind='server') {
  const file=path.join(root,'.runtime/server-control.lock');
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const nonce=crypto.randomUUID();
  for(let attempt=0;attempt<2;attempt++) {
    try {
      const fd=fs.openSync(file,'wx');
      try {fs.writeFileSync(fd,JSON.stringify({pid:process.pid,nonce,kind,created:new Date().toISOString()}));} finally {fs.closeSync(fd);}
      return ()=>{try{if(JSON.parse(fs.readFileSync(file,'utf8')).nonce===nonce)fs.unlinkSync(file);}catch{}};
    } catch(error) {
      if(error.code!=='EEXIST')throw error;
      let old;try{old=JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));}catch{throw Error('Otra operación está iniciando. Reintentá en unos segundos.');}
      if(!Number.isInteger(old.pid)||old.pid<1)throw Error('Revisá .runtime/server-control.lock: registro inválido.');
      let running=true;try{process.kill(old.pid,0);}catch(e){if(e.code==='ESRCH')running=false;}
      if(running)throw Error('Ya hay un arranque, servidor o respaldo en curso.');
      fs.unlinkSync(file);
    }
  }
  throw Error('No se pudo reservar el control del servidor.');
}
module.exports={acquire};
