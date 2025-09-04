import { categoryRules } from "./categoryRules";

export function getCategory(name: string): string {
  for (const rule of categoryRules) {
    for (const pattern of rule.patterns) {
      if (typeof pattern === "string") {
        if (name.includes(pattern)) {
          return rule.category;
        }
      } else {
        if (pattern.test(name)) {
          return rule.category;
        }
      }
    }
  }
  return "其他";
}

export default getCategory;
