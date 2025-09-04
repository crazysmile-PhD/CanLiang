import { useState } from "react";

export interface ItemTrendData {
  [date: string]: number;
}

export const useItemTrend = () => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [itemTrendData, setItemTrendData] = useState<ItemTrendData | null>(null);
  const [loadingTrend, setLoadingTrend] = useState(false);

  const handleItemClick = async (itemName: string) => {
    setSelectedItem(itemName);
    setLoadingTrend(true);
    try {
      const response = await fetch(`/api/item-trend?item=${encodeURIComponent(itemName)}`);
      if (response.ok) {
        const trendData = await response.json();
        setItemTrendData(trendData.data);
      } else {
        const mockTrendData: ItemTrendData = {
          "2025-05-20": 11,
        };
        setItemTrendData(mockTrendData);
      }
    } catch (err) {
      console.error("获取物品趋势数据失败:", err);
      const mockTrendData: ItemTrendData = {
        "2025-05-20": 11,
      };
      setItemTrendData(mockTrendData);
    } finally {
      setLoadingTrend(false);
    }
  };

  const closeItemModal = () => {
    setSelectedItem(null);
    setItemTrendData(null);
  };

  return { selectedItem, itemTrendData, loadingTrend, handleItemClick, closeItemModal };
};
