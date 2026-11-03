'use strict';

// One bounded health snapshot for the managed runner. It never starts or stops
// Minecraft and keeps the raw evidence local under .runtime/health.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const statePath = path.join(root, '.runtime/active-run.json');
const commandsPath = path.join(root, '.runtime/public-commands.txt');
const logPath = path.join(root, '.runtime/public-console.log');
const outDir = path.join(root, '.runtime/health');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  if (!fs.existsSync(statePath)) throw Error('No active-run state');
  const state = read(statePath);
  if (state.mode !== 'managed' || state.finished || !state.pid) throw Error('Managed server is not live');
  fs.mkdirSync(outDir, {recursive: true});
  const started = new Date().toISOString();
  const offset = fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8').length : 0;
  // Count pressure-prone entity classes without deleting or mutating entities.
  // The objective is reused so the snapshot stays bounded and machine-readable.
  const commands = [
    // The snapshot uses scoreboard commands. Suppress their operator feedback
    // while they run so players do not receive a chat flood every ten minutes.
    'gamerule sendCommandFeedback false',
    'spark health --memory',
    'spark tps',
    'scoreboard objectives add virgos_health dummy',
    'scoreboard players set #entities virgos_health 0',
    'execute as @e run scoreboard players add #entities virgos_health 1',
    'scoreboard players get #entities virgos_health',
    'scoreboard players set #items virgos_health 0',
    'execute as @e[type=minecraft:item] run scoreboard players add #items virgos_health 1',
    'scoreboard players get #items virgos_health',
    'scoreboard players set #villagers virgos_health 0',
    'execute as @e[type=minecraft:villager] run scoreboard players add #villagers virgos_health 1',
    'scoreboard players get #villagers virgos_health',
    'scoreboard players set #minecarts virgos_health 0',
    'execute as @e[type=minecraft:minecart] run scoreboard players add #minecarts virgos_health 1',
    'scoreboard players get #minecarts virgos_health',
    'list',
    'gamerule sendCommandFeedback true',
  ];
  fs.appendFileSync(commandsPath, commands.join('\n') + '\n', 'utf8');
  await sleep(3500);
  const log = fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8').slice(offset) : '';
  // Preserve a bounded tail so the numeric Spark values and scoreboard totals
  // remain together; filtering individual lines would drop the values below
  // headings such as `Memory usage:`.
  const evidence = log.split(/\r?\n/).slice(-240);
  const report = {schema: 1, startedUtc: started, finishedUtc: new Date().toISOString(), commands, state: read(statePath), evidence};
  const stamp = started.replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  fs.writeFileSync(path.join(outDir, `${stamp}.json`), JSON.stringify(report, null, 2) + '\n');
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
