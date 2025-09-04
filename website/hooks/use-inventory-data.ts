import { useState, useEffect } from "react"
import { InventoryData } from "@/types/inventory"

export function useInventoryData(selectedDate: string) {
  const [data, setData] = useState<InventoryData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedDate) return

      try {
        setLoading(true)
        const response = await fetch(`/api/analyse?date=${selectedDate}`)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        setData(data)
        setError(null)
      } catch (error) {
        console.error('Error fetching data:', error)
        setError('获取数据失败，请稍后再试')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [selectedDate])

  return { data, loading, error }
}
