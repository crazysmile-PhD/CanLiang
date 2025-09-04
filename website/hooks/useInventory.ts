import { useEffect, useState } from "react";

interface InventoryData {
  item_count: Record<string, number>;
  duration: string;
}

interface DateItem {
  value: string;
  label: string;
}

export function useDateList() {
  const [dates, setDates] = useState<DateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchDates = async () => {
      try {
        setLoading(true);
        const res = await fetch("/api/LogList");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        const list = data.list || [];
        const formatted = Array.isArray(list)
          ? list.map((d: string) => ({ value: d, label: d }))
          : [];
        if (!cancelled) {
          setDates(formatted);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError("获取日期列表失败，请稍后再试");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchDates();
    return () => {
      cancelled = true;
    };
  }, []);

  return { dates, loading, error };
}

export function useInventoryData(date: string) {
  const [data, setData] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!date) return;
    let cancelled = false;
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/analyse?date=${date}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const json = await res.json();
        if (!cancelled) {
          setData(json);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e.message);
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();
    return () => {
      cancelled = true;
    };
  }, [date]);

  return { data, loading, error };
}

