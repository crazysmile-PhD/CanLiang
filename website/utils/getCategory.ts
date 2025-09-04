import { categoryRules } from "./categoryRules";

export function getCategory(name: string): string {
  for (const { pattern, category } of categoryRules) {
    if (pattern.test(name)) {
      return category;
    }
  }
  return "其他";
}

export default getCategory;
