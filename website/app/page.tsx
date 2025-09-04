"use client"

import { useState, useEffect } from "react"
import { useDateList } from "@/hooks/useDateList"
import { useInventoryData } from "@/hooks/useInventoryData"
import { useItemTrend } from "@/hooks/useItemTrend"
import type { ItemTrendData } from "@/hooks/useItemTrend"
import { useStatModal } from "@/hooks/useStatModal"
import { colors, categoryColors } from "@/constants/colors"
import { rankingColors } from "@/constants/rankings"
import { categorizeItems, getCategoryTotals, getTopItems, filterAndSortItems, getTotalItemCount, getUniqueItemCount, generatePieChart, getItemColor } from "@/utils/inventory"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Search, BarChart2, CalendarIcon, Github, X, TrendingUp, Clock, Package } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { motion, AnimatePresence } from "framer-motion"

export default function InventoryPage() {
  const { dateList, selectedDate, setSelectedDate, loading: loadingDates, error: dateError } = useDateList()
  const { data, loading: loadingData, error: dataError } = useInventoryData(selectedDate)
  const { selectedItem, itemTrendData, loadingTrend, handleItemClick, closeItemModal } = useItemTrend()
  const { statModal, handleStatClick, closeStatModal } = useStatModal()
  const loading = loadingDates || loadingData
  const error = dateError || dataError
  const [searchTerm, setSearchTerm] = useState("")
  const [isChangingDate, setIsChangingDate] = useState(false)
  const [animationKey, setAnimationKey] = useState(0)
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  const handleDateChange = (newDate: string) => {
    if (newDate !== selectedDate) {
      setIsChangingDate(true)
      setTimeout(() => {
        setSelectedDate(newDate)
        setAnimationKey((prev) => prev + 1)
      }, 300)
    }
  }

  useEffect(() => {
    if (!loadingData) {
      setIsChangingDate(false)
    }
  }, [loadingData])

  const handleSelectAll = () => {
    setSelectedDate("all")
  }

  const handleSegmentHover = (index: number | null) => {
    setHoverIndex(index)
  }

 // 动画变体
 const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.5,
      when: "beforeChildren",
      staggerChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.3,
      when: "afterChildren",
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 },
  },
  exit: {
    y: -20,
    opacity: 0,
    transition: { duration: 0.2 },
  },
}

const chartVariants = {
  hidden: { scale: 0.9, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: { duration: 0.4, type: "spring", stiffness: 100 },
  },
  exit: {
    scale: 0.9,
    opacity: 0,
    transition: { duration: 0.3 },
  },
}
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="text-xl flex flex-col items-center"
        >
          <div className="w-12 h-12 border-4 border-t-transparent border-primary rounded-full animate-spin mb-4"></div>
          <div>加载中...</div>
        </motion.div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl text-red-500">错误: {error}</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl">无数据</div>
      </div>
    )
  }

  const categories = categorizeItems(data.item_count)
  const totalItems = getTotalItemCount(data.item_count)
  const uniqueItems = getUniqueItemCount(data.item_count)
  const duration = data.duration
  const top10Items = getTop5Items(data.item_count)
  const categoryTotals = getCategoryTotals(categories)
  const pieChartData = generatePieChart(categoryTotals)

   // 新增：处理扇形区域悬停
  const handleSegmentHover = (index: number | null) => {
    setHoverIndex(index)
  }

  // 找出最大数量，用于计算条形图比例
  const maxCount = top10Items[0][1]
  return (
    <div className="container mx-auto px-4 py-8 bg-white relative">
      {/* GitHub 图标 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="fixed top-6 right-6 z-50"
      >
        <motion.a
          href="https://github.com/Because66666/CanLiang"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center w-12 h-12 rounded-full shadow-lg transition-all duration-300 hover:shadow-xl"
          style={{
            backgroundColor: colors.light,
            border: `2px solid ${colors.lightBorder}`,
          }}
          whileHover={{
            scale: 1.1,
            backgroundColor: colors.primary,
            borderColor: colors.primary,
          }}
          whileTap={{ scale: 0.95 }}
        >
          <motion.div
            whileHover={{
              color: "#ffffff",
            }}
            transition={{ duration: 0.2 }}
          >
            <Github className="h-6 w-6" style={{ color: colors.secondary }} />
          </motion.div>
        </motion.a>
      </motion.div>

      {/* 物品详情模态框 */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={closeItemModal}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold" style={{ color: colors.secondary }}>
                  {selectedItem} - 数量趋势
                </h2>
                <button onClick={closeItemModal} className="p-2 rounded-full hover:bg-gray-100 transition-colors">
                  <X className="h-6 w-6" style={{ color: colors.secondary }} />
                </button>
              </div>

              {loadingTrend ? (
                <div className="flex items-center justify-center h-64">
                  <div
                    className="w-8 h-8 border-4 border-t-transparent rounded-full animate-spin"
                    style={{ borderColor: colors.primary, borderTopColor: "transparent" }}
                  ></div>
                </div>
              ) : itemTrendData ? (
                <TrendChart data={itemTrendData} title={selectedItem} colors={colors} type="item" />
              ) : (
                <div className="text-center text-gray-500 h-64 flex items-center justify-center">暂无趋势数据</div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 统计趋势模态框 */}
      <AnimatePresence>
        {statModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={closeStatModal}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold" style={{ color: colors.secondary }}>
                  {statModal.title}
                </h2>
                <button onClick={closeStatModal} className="p-2 rounded-full hover:bg-gray-100 transition-colors">
                  <X className="h-6 w-6" style={{ color: colors.secondary }} />
                </button>
              </div>

              {statModal.loading ? (
                <div className="flex items-center justify-center h-64">
                  <div
                    className="w-8 h-8 border-4 border-t-transparent rounded-full animate-spin"
                    style={{ borderColor: colors.primary, borderTopColor: "transparent" }}
                  ></div>
                </div>
              ) : statModal.data ? (
                <TrendChart data={statModal.data} title={statModal.title} colors={colors} type={statModal.type} />
              ) : (
                <div className="text-center text-gray-500 h-64 flex items-center justify-center">暂无趋势数据</div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.h1
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-8 text-3xl font-bold text-center"
        style={{ color: colors.secondary }}
      >
        参量质变仪
      </motion.h1>

      {/* 统计卡片 */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3"
      >
        <motion.div variants={itemVariants}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <Card
              className="border-0 shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200"
              style={{ backgroundColor: colors.light }}
              onClick={() => handleStatClick("totalItems")}
            >
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm" style={{ color: colors.secondary }}>
                    总物品数量
                  </p>
                  <p className="text-3xl font-bold" style={{ color: colors.darkText }}>
                    {totalItems}
                  </p>
                </div>
                <Package className="h-8 w-8" style={{ color: colors.primary }} />
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        <motion.div variants={itemVariants}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <Card
              className="border-0 shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200"
              style={{ backgroundColor: colors.light }}
              onClick={() => handleStatClick("duration")}
            >
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm" style={{ color: colors.secondary }}>
                    运行时间
                  </p>
                  <p className="text-3xl font-bold" style={{ color: colors.darkText }}>
                    {duration}
                  </p>
                </div>
                <Clock className="h-8 w-8" style={{ color: colors.primary }} />
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="border-0 shadow-sm overflow-hidden" style={{ backgroundColor: colors.light }}>
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <p className="text-sm" style={{ color: colors.secondary }}>
                  最多物品
                </p>
                <p className="text-3xl font-bold" style={{ color: colors.darkText }}>
                  {Object.entries(data.item_count).sort((a, b) => b[1] - a[1])[0][0]}
                </p>
              </div>
              <BarChart2 className="h-8 w-8" style={{ color: colors.primary }} />
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* 主要内容区域 - 分为左侧条形图和右侧物品列表 */}
      <div className="flex flex-col lg:flex-row gap-8">
        {/* 左侧图表 */}
        <div className="w-full lg:w-1/3 space-y-8">
          {/* 饼状图 */}
          <AnimatePresence mode="wait">
            <motion.div
              key={`pie-chart-${animationKey}`}
              variants={chartVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card className="border-0 shadow-sm overflow-hidden">
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-4" style={{ color: colors.secondary }}>
                    物品类别分布
                  </h2>
                  <div className="flex flex-col items-center">
                    <motion.div
                      className="relative w-[200px] h-[200px]"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      transition={{ duration: 0.8, type: "spring" }}
                    >
                      <svg viewBox="0 0 200 200" className="w-full h-full">
                        {pieChartData.map((segment, index) => {
                          if ("isFullCircle" in segment && segment.isFullCircle) {
                            return (
                              <motion.circle
                                key={index}
                                cx="100"
                                cy="100"
                                r="80"
                                fill={segment.color}
                                onMouseEnter={() => handleSegmentHover(index)}
                                onMouseLeave={() => handleSegmentHover(null)}
                                whileHover={{ scale: 1.15 }}
                                transition={{ type: "spring", stiffness: 300 }}
                              />
                            )
                          }

                          return (
                            <motion.path
                              key={index}
                              d={segment.path}
                              fill={segment.color}
                              stroke="white"
                              strokeWidth="1"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: 0.1 * index, duration: 0.5 }}
                              onMouseEnter={() => handleSegmentHover(index)}
                              onMouseLeave={() => handleSegmentHover(null)}
                              whileHover={{
                                scale: 1.15,
                                transformOrigin: "center",
                                transition: { type: "spring", stiffness: 300 },
                              }}
                            />
                          )
                        })}
                      </svg>
                    </motion.div>
                    {/* 图例部分修改 */}
                    <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-3 w-full">
                      {pieChartData.map((segment, index) => (
                        <motion.div
                          key={index}
                          className="flex items-center"
                          style={{
                            backgroundColor: hoverIndex === index ? "#f0f4ff" : "transparent",
                            borderRadius: 6,
                            padding: "4px 8px",
                          }}
                          onMouseEnter={() => handleSegmentHover(index)}
                          onMouseLeave={() => handleSegmentHover(null)}
                          transition={{ duration: 0.2 }}
                        >
                          <div
                            className="w-4 h-4 mr-2 flex-shrink-0 rounded-sm"
                            style={{ backgroundColor: segment.color }}
                          ></div>
                          <div className="flex justify-between w-full">
                            <motion.span
                              className="text-sm font-medium"
                              animate={{
                                fontWeight: hoverIndex === index ? 700 : 500,
                                scale: hoverIndex === index ? 1.05 : 1,
                                color: hoverIndex === index ? colors.primary : colors.secondary,
                              }}
                              transition={{ duration: 0.2 }}
                            >
                              {segment.name}
                            </motion.span>
                            <motion.span
                              className="text-sm"
                              animate={{
                                scale: hoverIndex === index ? 1.1 : 1,
                                color: hoverIndex === index ? colors.primary : colors.secondary,
                              }}
                              transition={{ duration: 0.2 }}
                            >
                              {segment.percentage}%
                            </motion.span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>

          {/* 条形图 */}
          <AnimatePresence mode="wait">
            <motion.div
              key={`bar-chart-${animationKey}`}
              variants={chartVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card className="border-0 shadow-sm overflow-hidden">
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-4" style={{ color: colors.secondary }}>
                    物品数量排行（前十五）
                  </h2>
                  <div className="space-y-4">
                    {top10Items.slice(0, 15).map(([name, count], index) => (
                      <motion.div
                        key={index}
                        className="flex flex-col"
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: index * 0.1, duration: 0.3 }}
                      >
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium truncate">{name}</span>
                          <span style={{ color: colors.secondary }}>{count}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-3">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(count / maxCount) * 100}%` }}
                            transition={{ duration: 0.8, delay: 0.2 + index * 0.1 }}
                            className="h-3 rounded-full"
                            style={{
                              backgroundColor: rankingColors[index % rankingColors.length],
                            }}
                          ></motion.div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* 右侧物品列表 */}
        <div className="w-full lg:w-2/3">
          {/* 搜索和日期选择区域 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 p-6 rounded-lg"
            style={{ backgroundColor: colors.light }}
          >
            <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-8">
              {/* 搜索 */}
              <div className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2">
                  <Search className="h-4 w-4" style={{ color: colors.primary }} />
                  <span className="text-sm" style={{ color: colors.secondary }}>
                    搜索物品:
                  </span>
                </div>
                <div className="relative w-full max-w-md">
                  <Input
                    placeholder="搜索物品..."
                    className="pl-4 py-3 border-0 shadow-sm focus:ring-2 w-[240px]"
                    style={{
                      borderColor: colors.lightBorder,
                      boxShadow: `0 0 0 1px ${colors.lightBorder}`,
                    }}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>

              {/* 日期选择 */}
              <div className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2">
                  <CalendarIcon className="h-4 w-4" style={{ color: colors.primary }} />
                  <span className="text-sm" style={{ color: colors.secondary }}>
                    选择日期:
                  </span>
                </div>
                <Select value={selectedDate} onValueChange={handleDateChange}>
                  <SelectTrigger
                    className="w-[240px] border-0 shadow-sm focus:ring-2"
                    style={{
                      borderColor: colors.lightBorder,
                      boxShadow: `0 0 0 1px ${colors.lightBorder}`,
                    }}
                  >
                    <SelectValue placeholder="选择日期" />
                  </SelectTrigger>
                  <SelectContent>
                    {dateList.map((date) => (
                      <SelectItem key={date.value} value={date.value}>
                        {date.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* "全部"按钮 */}
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 rounded-md text-sm font-medium shadow-sm"
                style={{
                  backgroundColor: selectedDate === "all" ? colors.primary : "#fff",
                  color: selectedDate === "all" ? "#fff" : colors.secondary,
                  boxShadow: `0 0 0 1px ${colors.lightBorder}`,
                }}
              >
                全部
              </button>
            </div>
          </motion.div>

          {/* 物品列表 */}
          <Tabs defaultValue="all" className="flex flex-col items-center">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
              <TabsList className="mb-6 p-1 rounded-md" style={{ backgroundColor: colors.lightGray }}>
                <TabsTrigger
                  value="all"
                  className="data-[state=active]:text-white"
                  style={{
                    backgroundColor: "transparent",
                    color: colors.secondary,
                    ["--tw-data-state-active-bg" as any]: colors.primary,
                  }}
                >
                  全部
                </TabsTrigger>
                {Object.keys(categories).map((category) => (
                  <TabsTrigger
                    key={category}
                    value={category}
                    className="data-[state=active]:text-white"
                    style={{
                      backgroundColor: "transparent",
                      color: colors.secondary,
                      ["--tw-data-state-active-bg" as any]: colors.primary,
                    }}
                  >
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>
            </motion.div>

            <div className="w-full">
              <AnimatePresence mode="wait">
                <TabsContent value="all">
                  <motion.div
                    key={`all-items-${animationKey}`}
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3"
                  >
                    {filterAndSortItems(data.item_count).map(([name, count], index) => (
                      <motion.div key={name} variants={itemVariants}>
                        <ItemCard
                          name={name}
                          count={count}
                          color={getItemColor(name)}
                          onClick={() => handleItemClick(name)}
                        />
                      </motion.div>
                    ))}
                  </motion.div>
                </TabsContent>

                {Object.entries(categories).map(([category, items]) => (
                  <TabsContent key={category} value={category}>
                    <motion.div
                      key={`${category}-items-${animationKey}`}
                      variants={containerVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3"
                    >
                      {filterAndSortItems(items).map(([name, count], index) => (
                        <motion.div key={name} variants={itemVariants}>
                          <ItemCard
                            name={name}
                            count={count}
                            color={categoryColors[category as keyof typeof categoryColors]}
                            onClick={() => handleItemClick(name)}
                          />
                        </motion.div>
                      ))}
                    </motion.div>
                  </TabsContent>
                ))}
              </AnimatePresence>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

function ItemCard({
  name,
  count,
  color,
  onClick,
}: { name: string; count: number; color: string; onClick: () => void }) {
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

function TrendChart({
  data,
  title,
  colors,
  type,
}: {
  data: ItemTrendData
  title: string
  colors: any
  type: "totalItems" | "duration" | "item"
}) {
  const sortedData = Object.entries(data).sort(([a], [b]) => a.localeCompare(b))
  const maxValue = Math.max(...Object.values(data))
  const minValue = Math.min(...Object.values(data))

  const chartWidth = 600
  const chartHeight = 300
  const padding = 60
  const innerWidth = chartWidth - 2 * padding
  const innerHeight = chartHeight - 2 * padding

  // 格式化数值显示
  const formatValue = (value: number) => {
    if (type === "duration") {
      // 将分钟数转换为时间格式
      const hours = Math.floor(value / 60)
      const minutes = value % 60
      return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
    }
    return value.toString()
  }

  // 计算点的位置
  const points = sortedData.map(([date, value], index) => {
    const x = padding + (index / (sortedData.length - 1)) * innerWidth
    const y = padding + ((maxValue - value) / (maxValue - minValue || 1)) * innerHeight
    return { x, y, date, value }
  })

  // 生成路径字符串
  const pathData = points.reduce((path, point, index) => {
    const command = index === 0 ? "M" : "L"
    return `${path} ${command} ${point.x} ${point.y}`
  }, "")

  // 生成渐变区域路径
  const areaPath = `${pathData} L ${points[points.length - 1].x} ${padding + innerHeight} L ${padding} ${padding + innerHeight} Z`

  // 获取图标
  const getIcon = () => {
    switch (type) {
      case "totalItems":
        return <Package className="h-5 w-5" style={{ color: colors.primary }} />
      case "duration":
        return <Clock className="h-5 w-5" style={{ color: colors.primary }} />
      default:
        return <TrendingUp className="h-5 w-5" style={{ color: colors.primary }} />
    }
  }

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center gap-2">
        {getIcon()}
        <span className="font-medium" style={{ color: colors.secondary }}>
          {type === "totalItems" ? "总物品数量变化趋势" : type === "duration" ? "运行时间变化趋势" : "数量变化趋势"}
        </span>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <svg width="100%" height="300" viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="overflow-visible">
          {/* 网格线 */}
          <defs>
            <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#e5e5e5" strokeWidth="1" />
            </pattern>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={colors.primary} stopOpacity="0.3" />
              <stop offset="100%" stopColor={colors.primary} stopOpacity="0.05" />
            </linearGradient>
          </defs>

          <rect x={padding} y={padding} width={innerWidth} height={innerHeight} fill="url(#grid)" />

          {/* Y轴标签 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = Math.round(minValue + (maxValue - minValue) * (1 - ratio))
            const y = padding + ratio * innerHeight
            return (
              <g key={ratio}>
                <line x1={padding - 5} y1={y} x2={padding} y2={y} stroke="#666" strokeWidth="1" />
                <text x={padding - 10} y={y + 4} textAnchor="end" fontSize="12" fill="#666">
                  {type === "duration" ? (value > 60 ? `${Math.floor(value / 60)}h` : `${value}m`) : value}
                </text>
              </g>
            )
          })}

          {/* 渐变区域 */}
          <path d={areaPath} fill="url(#areaGradient)" />

          {/* 折线 */}
          <motion.path
            d={pathData}
            fill="none"
            stroke={colors.primary}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
          />

          {/* 数据点 */}
          {points.map((point, index) => (
            <motion.g key={index}>
              <motion.circle
                cx={point.x}
                cy={point.y}
                r="4"
                fill="white"
                stroke={colors.primary}
                strokeWidth="3"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 + 0.5, duration: 0.3 }}
                whileHover={{ scale: 1.5 }}
              />

              {/* X轴标签 */}
              <text
                x={point.x}
                y={padding + innerHeight + 20}
                textAnchor="middle"
                fontSize="11"
                fill="#666"
                transform={`rotate(-45, ${point.x}, ${padding + innerHeight + 20})`}
              >
                {point.date.slice(4)} {/* 只显示月-日 */}
              </text>

              {/* 悬停提示 */}
              <motion.g opacity={0} whileHover={{ opacity: 1 }} transition={{ duration: 0.2 }}>
                <rect x={point.x - 35} y={point.y - 35} width="70" height="25" fill="rgba(0,0,0,0.8)" rx="4" />
                <text x={point.x} y={point.y - 18} textAnchor="middle" fontSize="12" fill="white">
                  {formatValue(point.value)}
                </text>
              </motion.g>
            </motion.g>
          ))}

          {/* 坐标轴 */}
          <line x1={padding} y1={padding} x2={padding} y2={padding + innerHeight} stroke="#333" strokeWidth="2" />
          <line
            x1={padding}
            y1={padding + innerHeight}
            x2={padding + innerWidth}
            y2={padding + innerHeight}
            stroke="#333"
            strokeWidth="2"
          />
        </svg>
      </div>

      {/* 统计信息 */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div className="p-3 rounded-lg" style={{ backgroundColor: colors.light }}>
          <div className="text-sm" style={{ color: colors.secondary }}>
            最大值
          </div>
          <div className="text-xl font-bold" style={{ color: colors.darkText }}>
            {formatValue(maxValue)}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: colors.light }}>
          <div className="text-sm" style={{ color: colors.secondary }}>
            最小值
          </div>
          <div className="text-xl font-bold" style={{ color: colors.darkText }}>
            {formatValue(minValue)}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: colors.light }}>
          <div className="text-sm" style={{ color: colors.secondary }}>
            平均值
          </div>
          <div className="text-xl font-bold" style={{ color: colors.darkText }}>
            {formatValue(Math.round(Object.values(data).reduce((a, b) => a + b, 0) / Object.values(data).length))}
          </div>
        </div>
      </div>
    </div>
  )
}
