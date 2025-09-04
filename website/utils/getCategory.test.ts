import { describe, it } from "node:test";
import { strict as assert } from "node:assert";
import { getCategory } from "./getCategory";

describe("getCategory", () => {
  it("categorizes artifacts by keyword", () => {
    assert.equal(getCategory("冒险家的花"), "圣遗物");
  });

  it("categorizes artifacts by component name", () => {
    assert.equal(getCategory("勇者的沙漏"), "圣遗物");
  });

  it("categorizes minerals", () => {
    assert.equal(getCategory("铁块"), "矿物");
  });

  it("categorizes food", () => {
    assert.equal(getCategory("苹果"), "食材");
  });

  it("defaults to other when no rule matches", () => {
    assert.equal(getCategory("未知物品"), "其他");
  });
});
