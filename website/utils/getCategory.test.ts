import assert from 'assert'
import { getCategory } from './getCategory'

assert.strictEqual(getCategory('冒险家的花'), '圣遗物')
assert.strictEqual(getCategory('作家笔记'), '其他')

console.log('All tests passed')
