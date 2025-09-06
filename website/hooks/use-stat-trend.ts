import { useState } from "react"
import { ItemTrendData, StatModalData } from "@/types/inventory"

export function useStatTrend() {
  const [statModal, setStatModal] = useState<StatModalData | null>(null)

  const generateMockTrendData = (type: "totalItems" | "duration"): ItemTrendData => {
    const mockData: ItemTrendData = {"20250520":10}
    return mockData
  }

  const handleStatClick = async (type: "totalItems" | "duration") => {
    const titles = {
      totalItems: "总物品数量趋势",
      duration: "运行时间趋势",
    }

    setStatModal({
      type,
      title: titles[type],
      data: null,
      loading: true,
    })

    try {
      const apiEndpoint = type === "totalItems" ? "/api/total-items-trend" : "/api/duration-trend"
      const response = await fetch(apiEndpoint)

      if (response.ok) {
        const trendData = await response.json()
        setStatModal((prev) => (prev ? { ...prev, data: trendData.data, loading: false } : null))
      } else {
        const mockTrendData: ItemTrendData = generateMockTrendData(type)
        setStatModal((prev) => (prev ? { ...prev, data: mockTrendData, loading: false } : null))
      }
    } catch (error) {
      console.error(`获取${titles[type]}数据失败:`, error)
      const mockTrendData: ItemTrendData = generateMockTrendData(type)
      setStatModal((prev) => (prev ? { ...prev, data: mockTrendData, loading: false } : null))
    }
  }

  const closeStatModal = () => {
    setStatModal(null)
  }

  return { statModal, handleStatClick, closeStatModal }
}
