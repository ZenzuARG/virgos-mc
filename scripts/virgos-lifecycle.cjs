'use strict';
const fs = require('node:fs');
const path = require('node:path');

// This helper never records Minecraft commands or credentials.
function validCheckpoint(request, started, now = Date.now()) {
  if (!request || request.schema !== 1 || request.reason !== 'full-backup') return false;
  const requested = Date.parse(request.requestedAt);
  const beginning = Date.parse(started);
  return Number.isFinite(requested) && Number.isFinite(beginning) &&
    requested >= beginning && requested <= now && now - requested < 15 * 60 * 1000;
}
function classifyExit(code, intentionalStop, request, started, now = Date.now()) {
  const checkpoint = code === 0 && validCheckpoint(request, started, now);
  return { unexpected: !intentionalStop && !checkpoint, checkpoint,
    stopObserved: Boolean(intentionalStop), cleanExit: code === 0 };
}
function readCheckpoint(root) {
  try { return JSON.parse(fs.readFileSync(path.join(root, '.runtime/checkpoint-request.json'), 'utf8').replace(/^\uFEFF/, '')); }
  catch { return null; }
}
function createAudit(root) {
  const file = path.join(root, '.runtime/control-audit.jsonl');
  const allowed = new Set(['runner','javaPid','started','code','signal','unexpected','checkpoint',
    'stopObserved','cleanExit','javaVersion','source','collector']);
  return function audit(event, data = {}) {
    try {
      const clean = { at: new Date().toISOString(), event };
      for (const [k,v] of Object.entries(data)) if (allowed.has(k)) clean[k] = v;
      if (fs.existsSync(file) && fs.statSync(file).size > 256 * 1024) {
        const old = file + '.1';
        if (fs.existsSync(old)) fs.unlinkSync(old);
        fs.renameSync(file, old);
      }
      fs.appendFileSync(file, JSON.stringify(clean) + '\n', 'utf8');
    } catch (error) { console.error('No se pudo escribir auditoria de control:', error.code || 'IO_ERROR'); }
  };
}
module.exports = { validCheckpoint, classifyExit, readCheckpoint, createAudit };
