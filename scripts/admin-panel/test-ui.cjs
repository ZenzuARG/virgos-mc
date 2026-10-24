'use strict';
// Uses the development runtime's Playwright; the panel itself has no dependencies.
const {chromium}=require(process.argv[2]||'playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {Controller}=require('./core.cjs');
(async()=>{
  const root=path.resolve(__dirname,'../..'),out=path.join(root,'.lab/admin-panel');fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  const c=new Controller(root);let created=false;
  try {
    await page.goto('http://127.0.0.1:8765');await page.locator('#status-title').filter({hasText:'Abierto'}).waitFor();
    assert.equal(await page.locator('[data-action=start]').isEnabled(),false);
    await page.screenshot({path:path.join(out,'overview.png'),fullPage:true});
    await page.locator('[data-action=stop]').click();await page.locator('#confirm-dialog').waitFor({state:'visible'});await page.getByRole('button',{name:'Cancelar',exact:true}).click();assert.equal((await c.status()).state,'online');
    await page.locator('[data-tab=console]').click();await page.locator('#command').fill('list');await page.getByRole('button',{name:'Enviar ↗'}).click();await page.locator('#confirm-ok').click();await page.waitForTimeout(1800);await page.waitForFunction(()=>document.getElementById('console-log').textContent.includes('players online'));
    await page.locator('[data-tab=players]').click();await page.locator('.player-select').filter({hasText:'ZenzuCarry'}).click();await page.locator('#player-detail h3').filter({hasText:'ZenzuCarry'}).waitFor();await page.screenshot({path:path.join(out,'players.png'),fullPage:true});
    await page.locator('[data-tab=permissions]').click();await page.locator('#refresh-permissions').click();await page.waitForTimeout(1000);
    await page.locator('#new-group').fill('panel_test');await page.getByRole('button',{name:'Crear',exact:true}).click();await page.locator('#confirm-ok').click();created=true;
    await page.waitForFunction(()=>[...document.getElementById('group-choice').options].some(o=>o.value==='panel_test'));
    await page.locator('#permission-kind').selectOption('group');await page.locator('#permission-target').selectOption('panel_test');await page.locator('#permission-node').fill('virgos.panel.test');await page.locator('#permission-value').selectOption('false');await page.locator('#permission-apply').click();await page.locator('#confirm-ok').click();
    await page.waitForFunction(()=>document.getElementById('permission-nodes').textContent.includes('virgos.panel.test'));
    const saved=c.permissions();assert.equal(saved.groups.panel_test.nodes[0].value,false);assert.equal(saved.groups.panel_test.nodes[0].key,'virgos.panel.test');
    await page.screenshot({path:path.join(out,'permissions.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});await page.locator('[data-tab=overview]').click();await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'ui-result.json'),JSON.stringify({passed:true,checks:['live status','cancel shutdown','console list and response','player profile','LuckPerms group creation','LuckPerms deny and readback','mobile layout','no browser errors'],testedAt:new Date().toISOString()},null,2));console.log('UI checks passed, including live LuckPerms readback.');
  } finally {
    if(created){c.queue('lp deletegroup panel_test');await new Promise(r=>setTimeout(r,800));await c.refreshPermissions();assert.equal(c.permissions().groups.panel_test,undefined);}
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
