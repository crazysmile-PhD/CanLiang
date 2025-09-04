export interface CategoryRule {
  pattern: RegExp;
  category: string;
}

export const categoryRules: CategoryRule[] = [
  {
    pattern: /(冒险家|游医|幸运儿|险家|医的|运儿|家|的方巾|的枭羽|的怀钟|的药壶|的银莲|的怀表|的尾羽|的头带|的金杯|的之花|的之杯|的沙漏|的绿花|的银冠|的鹰羽)/,
    category: "圣遗物",
  },
  {
    pattern: /^(铁块|白铁块|水晶块|魔晶块|星银矿石|紫晶块|萃凝晶)$/,
    category: "矿物",
  },
  {
    pattern: /^(苹果|蘑菇|甜甜花|胡萝卜|白萝卜|金鱼草|薄荷|松果|树莓|松茸|鸟蛋|海草|堇瓜|墩墩桃|须弥蔷薇|枣椰|茉洁草|沉玉仙茗|颗粒果|澄晶实|红果果菇|小灯草|嘟嘟莲|莲蓬|绝云椒椒|清心|马尾|琉璃袋|竹笋|绯樱绣球|树王圣体菇|帕蒂沙兰|青蜜莓)$/,
    category: "食材",
  },
];
