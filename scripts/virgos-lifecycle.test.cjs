'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { isOtherProcessAlive } = require('./virgos-lifecycle.cjs');

test('restart does not reject the current runner as an active owner', () => {
  let probed = false;
  assert.equal(isOtherProcessAlive(42, 42, () => { probed = true; }), false);
  assert.equal(probed, false);
});

test('restart rejects a different live runner', () => {
  assert.equal(isOtherProcessAlive(42, 99, () => {}), true);
});

test('restart ignores a stale runner process', () => {
  assert.equal(isOtherProcessAlive(42, 99, () => { throw Object.assign(new Error('gone'), { code: 'ESRCH' }); }), false);
});
