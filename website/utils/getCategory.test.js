const test = require('node:test');
const assert = require('node:assert/strict');
const { getCategory } = require('./dist/getCategory.js');

test('categorizes artifacts', () => {
  assert.equal(getCategory('冒险家之花'), '圣遗物');
});

test('categorizes minerals', () => {
  assert.equal(getCategory('铁块'), '矿物');
});

test('categorizes food', () => {
  assert.equal(getCategory('苹果'), '食材');
});

test('falls back to 其他 for unknown items', () => {
  assert.equal(getCategory('未知物品'), '其他');
});

test('does not match partial names', () => {
  assert.equal(getCategory('大苹果'), '其他');
});
