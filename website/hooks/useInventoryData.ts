import { useState, useEffect } from "react";

export interface InventoryData {
  item_count: Record<string, number>;
  duration: string;
}

export const useInventoryData = (selectedDate: string) => {
  const [data, setData] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedDate) return;
      try {
        setLoading(true);
        const response = await fetch(`/api/analyse?date=${selectedDate}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("获取数据失败，请稍后再试");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedDate]);

  return { data, loading, error };
};
