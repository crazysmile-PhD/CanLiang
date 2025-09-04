import { getCategory, categorizeItems, getCategoryTotals, generatePieChart, categoryColors } from '@/lib/inventory';

describe('inventory utilities', () => {
  test('getCategory categorizes names correctly', () => {
    expect(getCategory('苹果')).toBe('食材');
    expect(getCategory('铁块')).toBe('矿物');
    expect(getCategory('冒险家之花')).toBe('圣遗物');
    expect(getCategory('未知物')).toBe('其他');
  });

  test('categorizeItems groups items by category', () => {
    const items = { 苹果: 2, 铁块: 3, 未知物: 1 };
    const categories = categorizeItems(items);
    expect(categories['食材']['苹果']).toBe(2);
    expect(categories['矿物']['铁块']).toBe(3);
    expect(categories['其他']['未知物']).toBe(1);
  });

  test('getCategoryTotals computes totals with colors', () => {
    const items = { 苹果: 2, 铁块: 3 };
    const categories = categorizeItems(items);
    const totals = getCategoryTotals(categories);
    expect(totals).toContainEqual({ name: '食材', count: 2, color: categoryColors['食材'] });
    expect(totals).toContainEqual({ name: '矿物', count: 3, color: categoryColors['矿物'] });
  });

  test('generatePieChart handles single category', () => {
    const data = [{ name: '食材', count: 5, color: categoryColors['食材'] }];
    const chart = generatePieChart(data);
    expect(chart[0].isFullCircle).toBe(true);
    expect(chart[0].percentage).toBe('100.0');
  });

  test('generatePieChart creates segments for multiple categories', () => {
    const data = [
      { name: '食材', count: 5, color: categoryColors['食材'] },
      { name: '矿物', count: 5, color: categoryColors['矿物'] },
    ];
    const chart = generatePieChart(data);
    expect(chart).toHaveLength(2);
    expect(chart[0]).toHaveProperty('path');
  });
});
