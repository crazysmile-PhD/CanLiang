export type Category = "圣遗物" | "矿物" | "食材" | "其他";

interface Rule {
  category: Category;
  match: (name: string) => boolean;
}

const artifactSetNames = ["冒险家", "游医", "幸运儿"];

const artifactPieceRegex = /的(方巾|枭羽|怀钟|药壶|银莲|怀表|尾羽|头带|金杯|之花|之杯|沙漏|绿花|银冠|鹰羽)$/;

export const categoryRules: Rule[] = [
  {
    category: "圣遗物",
    match: (name: string) =>
      artifactSetNames.some(set => name.includes(set)) ||
      artifactPieceRegex.test(name),
  },
  {
    category: "矿物",
    match: (name: string) =>
      ["铁块", "白铁块", "水晶块", "魔晶块", "星银矿石", "紫晶块", "萃凝晶"].includes(name),
  },
  {
    category: "食材",
    match: (name: string) =>
      [
        "苹果", "蘑菇", "甜甜花", "胡萝卜", "白萝卜", "金鱼草", "薄荷",
        "松果", "树莓", "松茸", "鸟蛋", "海草", "堇瓜", "墩墩桃",
        "须弥蔷薇", "枣椰", "茉洁草", "沉玉仙茗", "颗粒果", "澄晶实",
        "红果果菇", "小灯草", "嘟嘟莲", "莲蓬", "绝云椒椒", "清心",
        "马尾", "琉璃袋", "竹笋", "绯樱绣球", "树王圣体菇", "帕蒂沙兰",
        "青蜜莓",
      ].includes(name),
  },
];

export function getCategoryFromRules(name: string): Category {
  const rule = categoryRules.find(r => r.match(name));
  return rule ? rule.category : "其他";
}
