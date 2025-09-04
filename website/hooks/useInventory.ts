import { useEffect, useState } from 'react'

interface InventoryData {
  item_count: Record<string, number>
  duration: string
}

export function useInventory(date: string) {
  const [data, setData] = useState<InventoryData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!date) return
    setLoading(true)
    fetch(`/api/analyse?date=${date}`)
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok')
        return res.json()
      })
      .then((json) => {
        setData(json)
        setError(null)
      })
      .catch((err) => {
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [date])

  return { data, loading, error }
}
