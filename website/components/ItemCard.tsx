import { Card, CardContent } from "@/components/ui/card"
import { motion } from "framer-motion"

export interface ItemCardProps {
  name: string
  count: number
  color: string
  onClick: () => void
}

export default function ItemCard({ name, count, color, onClick }: ItemCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Card
        className="border border-gray-100 hover:shadow-md transition-shadow duration-200 cursor-pointer"
        onClick={onClick}
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="truncate font-medium">{name}</div>
            <div
              className="ml-2 rounded-full px-2 py-1 text-xs font-semibold text-white"
              style={{ backgroundColor: color }}
            >
              {count}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
