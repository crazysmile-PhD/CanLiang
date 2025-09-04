import { getCategory, categorizeItems, getCategoryTotals, generatePieChart, categoryColors } from '@/lib/inventory'

describe('inventory utils', () => {
  test('getCategory returns correct category', () => {
    expect(getCategory('冒险家之花')).toBe('圣遗物')
    expect(getCategory('铁块')).toBe('矿物')
    expect(getCategory('苹果')).toBe('食材')
    expect(getCategory('未知物品')).toBe('其他')
  })

  test('categorizeItems groups items by category', () => {
    const items = { '苹果': 2, '铁块': 1, '未知物品': 3 }
    const categories = categorizeItems(items)
    expect(categories['食材']).toHaveProperty('苹果', 2)
    expect(categories['矿物']).toHaveProperty('铁块', 1)
    expect(categories['其他']).toHaveProperty('未知物品', 3)
  })

  test('getCategoryTotals aggregates counts', () => {
    const categories = {
      食材: { 苹果: 2 },
      矿物: { 铁块: 1 },
      圣遗物: {},
      其他: { 未知物品: 3 },
    }
    const totals = getCategoryTotals(categories)
    expect(totals).toEqual([
      { name: '食材', count: 2, color: categoryColors['食材'] },
      { name: '矿物', count: 1, color: categoryColors['矿物'] },
      { name: '圣遗物', count: 0, color: categoryColors['圣遗物'] },
      { name: '其他', count: 3, color: categoryColors['其他'] },
    ])
  })

  test('generatePieChart returns segments with percentages', () => {
    const totals = [
      { name: '食材', count: 2, color: '#f39c12' },
      { name: '矿物', count: 2, color: '#4CAF50' },
    ]
    const chart = generatePieChart(totals)
    expect(chart).toHaveLength(2)
    expect(chart[0]).toHaveProperty('path')
    expect(chart[0]).toHaveProperty('percentage', '50.0')
  })
})
