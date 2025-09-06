export interface InventoryData {
  item_count: Record<string, number>
  duration: string
}

export interface DateItem {
  value: string
  label: string
}

export interface CategoryTotal {
  name: string
  count: number
  color: string
}

export interface ItemTrendData {
  [date: string]: number
}

export interface StatModalData {
  type: "totalItems" | "duration" | "item"
  title: string
  data: ItemTrendData | null
  loading: boolean
}
