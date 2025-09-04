import { useState } from "react";

export interface ItemTrendData {
  [date: string]: number;
}

export interface StatModalData {
  type: "totalItems" | "duration" | "item";
  title: string;
  data: ItemTrendData | null;
  loading: boolean;
}

const generateMockTrendData = (type: "totalItems" | "duration"): ItemTrendData => {
  return { "20250520": 10 };
};

export const useStatModal = () => {
  const [statModal, setStatModal] = useState<StatModalData | null>(null);

  const handleStatClick = async (type: "totalItems" | "duration") => {
    const titles = {
      totalItems: "总物品数量趋势",
      duration: "运行时间趋势",
    };

    setStatModal({ type, title: titles[type], data: null, loading: true });

    try {
      const apiEndpoint =
        type === "totalItems" ? "/api/total-items-trend" : "/api/duration-trend";
      const response = await fetch(apiEndpoint);
      if (response.ok) {
        const trendData = await response.json();
        setStatModal((prev) =>
          prev ? { ...prev, data: trendData.data, loading: false } : null
        );
      } else {
        const mockTrendData = generateMockTrendData(type);
        setStatModal((prev) =>
          prev ? { ...prev, data: mockTrendData, loading: false } : null
        );
      }
    } catch (err) {
      console.error(`获取${titles[type]}数据失败:`, err);
      const mockTrendData = generateMockTrendData(type);
      setStatModal((prev) =>
        prev ? { ...prev, data: mockTrendData, loading: false } : null
      );
    }
  };

  const closeStatModal = () => setStatModal(null);

  return { statModal, handleStatClick, closeStatModal };
};
