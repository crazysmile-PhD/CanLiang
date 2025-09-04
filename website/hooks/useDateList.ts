import { useState, useEffect } from "react";

export interface DateItem {
  value: string;
  label: string;
}

export const useDateList = () => {
  const [dateList, setDateList] = useState<DateItem[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDateList = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/LogList");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();
        const dates = responseData.list || [];
        const formattedDates = Array.isArray(dates)
          ? dates.map((date: string) => ({ value: date, label: date }))
          : [];
        setDateList(formattedDates);
        if (formattedDates.length > 0) {
          setSelectedDate(formattedDates[0].value);
        }
        setError(null);
      } catch (err) {
        console.error("Error fetching date list:", err);
        setError("获取日期列表失败，请稍后再试");
      } finally {
        setLoading(false);
      }
    };
    fetchDateList();
  }, []);

  return { dateList, selectedDate, setSelectedDate, loading, error };
};
