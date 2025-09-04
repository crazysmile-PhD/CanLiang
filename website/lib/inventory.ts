export interface CategoryTotal {
  name: string
  count: number
  color: string
}

export const categoryColors = {
  圣遗物: "#34495e",
  矿物: "#4CAF50",
  食材: "#f39c12",
  其他: "#bdc3c7",
}

export const getCategory = (name: string): string => {
  if (
    name.includes("冒险家") ||
    name.includes("游医") ||
    name.includes("幸运儿") ||
    name.includes("险家") ||
    name.includes("医的") ||
    name.includes("运儿") ||
    name.includes("家") ||
    (name.includes("的") &&
      (name.includes("方巾") ||
        name.includes("枭羽") ||
        name.includes("怀钟") ||
        name.includes("药壶") ||
        name.includes("银莲") ||
        name.includes("怀表") ||
        name.includes("尾羽") ||
        name.includes("头带") ||
        name.includes("金杯") ||
        name.includes("之花") ||
        name.includes("之杯") ||
        name.includes("沙漏") ||
        name.includes("绿花") ||
        name.includes("银冠") ||
        name.includes("鹰羽")))
  ) {
    return "圣遗物"
  } else if (["铁块", "白铁块", "水晶块", "魔晶块", "星银矿石", "紫晶块", "萃凝晶"].includes(name)) {
    return "矿物"
  } else if (
    [
      "苹果", "蘑菇", "甜甜花", "胡萝卜", "白萝卜", "金鱼草", "薄荷",
      "松果", "树莓", "松茸", "鸟蛋", "海草", "堇瓜", "墩墩桃",
      "须弥蔷薇", "枣椰", "茉洁草", "沉玉仙茗", "颗粒果", "澄晶实",
      "红果果菇", "小灯草", "嘟嘟莲", "莲蓬", "绝云椒椒", "清心",
      "马尾", "琉璃袋", "竹笋", "绯樱绣球", "树王圣体菇", "帕蒂沙兰",
      "青蜜莓"
    ].includes(name)
  ) {
    return "食材"
  } else {
    return "其他"
  }
}

export const categorizeItems = (items: Record<string, number>) => {
  const categories: Record<string, Record<string, number>> = {
    圣遗物: {},
    矿物: {},
    食材: {},
    其他: {},
  }

  Object.entries(items).forEach(([name, count]) => {
    const category = getCategory(name)
    categories[category][name] = count
  })

  return categories
}

export const getCategoryTotals = (
  categories: Record<string, Record<string, number>>
): CategoryTotal[] => {
  const totals: CategoryTotal[] = []
  Object.entries(categories).forEach(([name, items]) => {
    const count = Object.values(items).reduce((sum, c) => sum + c, 0)
    totals.push({
      name,
      count,
      color: categoryColors[name as keyof typeof categoryColors],
    })
  })
  return totals
}

export const generatePieChart = (data: CategoryTotal[]) => {
  const total = data.reduce((sum, item) => sum + item.count, 0)
  const nonZeroItems = data.filter(item => item.count > 0)
  if (nonZeroItems.length === 1) {
    const item = nonZeroItems[0]
    return [
      {
        isFullCircle: true,
        color: item.color,
        name: item.name,
        count: item.count,
        percentage: '100.0',
        path: '',
      },
    ]
  }

  let currentAngle = 0
  return data.map(item => {
    const percentage = item.count / total
    const startAngle = currentAngle
    const endAngle = currentAngle + percentage * 2 * Math.PI

    const x1 = 100 + 80 * Math.cos(startAngle)
    const y1 = 100 + 80 * Math.sin(startAngle)
    const x2 = 100 + 80 * Math.cos(endAngle)
    const y2 = 100 + 80 * Math.sin(endAngle)
    const largeArcFlag = percentage > 0.5 ? 1 : 0
    const path = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2} Z`
    currentAngle = endAngle
    return {
      path,
      color: item.color,
      name: item.name,
      count: item.count,
      percentage: (percentage * 100).toFixed(1),
    }
  })
}

export const getItemColor = (name: string) => {
  const category = getCategory(name)
  return categoryColors[category as keyof typeof categoryColors]
}
