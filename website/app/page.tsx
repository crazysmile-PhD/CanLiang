"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Search, BarChart2, CalendarIcon, Github, X, Clock, Package } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { motion, AnimatePresence } from "framer-motion"
import { ItemCard } from "@/components/ItemCard"
import { TrendChart } from "@/components/TrendChart"
import { CategoryTotal, getCategory, categorizeItems, getCategoryTotals, generatePieChart, categoryColors } from "@/lib/inventory"

interface InventoryData {
  item_count: Record<string, number>
  duration: string
}

interface DateItem {
  value: string
  label: string
}

interface ItemTrendData {
  [date: string]: number
}

interface StatModalData {
  type: "totalItems" | "duration" | "item"
  title: string
  data: ItemTrendData | null
  loading: boolean
}

export default function InventoryPage() {
  const [dateList, setDateList] = useState<DateItem[]>([])
  const [selectedDate, setSelectedDate] = useState<string>("") 
  const [data, setData] = useState<InventoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [isChangingDate, setIsChangingDate] = useState(false)
  const [animationKey, setAnimationKey] = useState(0)
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)
  const [selectedItem, setSelectedItem] = useState<string | null>(null)
  const [itemTrendData, setItemTrendData] = useState<ItemTrendData | null>(null)
  const [loadingTrend, setLoadingTrend] = useState(false)
  const [statModal, setStatModal] = useState<StatModalData | null>(null)


  // 定义颜色方案
  const colors = {
    primary: "#3498db", // 主色调：蓝色
    secondary: "#2c3e50", // 次要色调：深蓝
    accent1: "#4CAF50", // 强调色1：绿色
    accent2: "#f39c12", // 强调色2：橙色
    light: "#e6f2ff", // 浅色背景
    lightBorder: "#85b8e8", // 浅色边框
    lightGray: "#f5f5f5", // 浅灰色
    mediumGray: "#bdc3c7", // 中灰色
    darkText: "#003366", // 深色文字
  }

  // 定义排行榜颜色
  const rankingColors = [
    "#3498db", // 蓝色
    "#27ae60", // 绿色
    "#f39c12", // 橙色
    "#9b59b6", // 紫色
    "#e74c3c", // 红色
    "#1abc9c", // 青色
    "#d35400", // 深橙色
    "#2980b9", // 深蓝色
    "#8e44ad", // 深紫色
    "#c0392b", // 深红色
  ]

  // 处理统计卡片点击
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
      // 调用相应的API获取趋势数据
      const apiEndpoint = type === "totalItems" ? "/api/total-items-trend" : "/api/duration-trend"
      const response = await fetch(apiEndpoint)

      if (response.ok) {
        const trendData = await response.json()
        setStatModal((prev) => (prev ? { ...prev, data: trendData.data, loading: false } : null))
      } else {
        // 如果API调用失败，使用模拟数据
        const mockTrendData: ItemTrendData = generateMockTrendData(type)
        setStatModal((prev) => (prev ? { ...prev, data: mockTrendData, loading: false } : null))
      }
    } catch (error) {
      console.error(`获取${titles[type]}数据失败:`, error)
      // 使用模拟数据作为备选
      const mockTrendData: ItemTrendData = generateMockTrendData(type)
      setStatModal((prev) => (prev ? { ...prev, data: mockTrendData, loading: false } : null))
    }
  }

  // 生成模拟趋势数据
  const generateMockTrendData = (type: "totalItems" | "duration"): ItemTrendData => {
    const dates = [
      "20250520",
    ]
    const mockData: ItemTrendData = {"20250520":10}
    return mockData
  }

  // 处理物品点击
  const handleItemClick = async (itemName: string) => {
    setSelectedItem(itemName)
    setLoadingTrend(true)

    try {
      // 调用API获取物品趋势数据
      const response = await fetch(`/api/item-trend?item=${encodeURIComponent(itemName)}`)
      if (response.ok) {
        const trendData = await response.json()
        setItemTrendData(trendData.data)
      } else {
        // 如果API调用失败，使用模拟数据
        const mockTrendData: ItemTrendData = {
          "2025-05-20": 11,
        }
        setItemTrendData(mockTrendData)
      }
    } catch (error) {
      console.error("获取物品趋势数据失败:", error)
      // 使用模拟数据作为备选
      const mockTrendData: ItemTrendData = {
        "2025-05-20": 11,
      }
      setItemTrendData(mockTrendData)
    } finally {
      setLoadingTrend(false)
    }
  }

  // 关闭物品详情模态框
  const closeItemModal = () => {
    setSelectedItem(null)
    setItemTrendData(null)
  }
    // 关闭统计模态框
  const closeStatModal = () => {
    setStatModal(null)
  }

    // 处理日期变化
  const handleDateChange = (newDate: string) => {
      if (newDate !== selectedDate) {
        setIsChangingDate(true)
  
        // 短暂延迟以允许退出动画完成
        setTimeout(() => {
          setSelectedDate(newDate)
          setAnimationKey((prev) => prev + 1)
  
          // 模拟数据加载
          setLoading(true)
          setTimeout(() => {
            setLoading(false)
            setIsChangingDate(false)
          }, 600)
        }, 300)
      }
    }

  // 从API获取日期列表
  useEffect(() => {
    const fetchDateList = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/LogList')
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const responseData = await response.json()
        // 从返回的JSON中提取日期列表
        const dates = responseData.list || []
        // 将日期转换为Select组件需要的格式
        const formattedDates = Array.isArray(dates) ? dates.map(date => ({
          value: date,
          label: date
        })) : []
        
        setDateList(formattedDates)
        
        // 设置第一个日期为默认选中日期
        if (formattedDates.length > 0) {
          setSelectedDate(formattedDates[0].value)
        }
        
        setError(null)
      } catch (error) {
        console.error('Error fetching date list:', error)
        setError('获取日期列表失败，请稍后再试')
      } finally {
        setLoading(false)
      }
    }

    fetchDateList()
  }, [])

  const handleSelectAll = () => {
    setSelectedDate('all')  // 设定一个特殊值来表示“全部”
  }

  // 获取物品数据
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

  // 过滤和排序物品
  const getTop5Items = (items: Record<string, number>) => {
    return Object.entries(items)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
  }

  // 过滤和排序物品 (默认按数量排序)
  const filterAndSortItems = (items: Record<string, number>) => {
    return Object.entries(items)
      .filter(([name]) => name.toLowerCase().includes(searchTerm.toLowerCase()))
      .sort((a, b) => b[1] - a[1])
  }

  // 获取总物品数量
  const getTotalItemCount = (items: Record<string, number>) => {
    return Object.values(items).reduce((sum, count) => sum + count, 0)
  }

  // 获取物品种类数量
  const getUniqueItemCount = (items: Record<string, number>) => {
    return Object.keys(items).length
  }

  const getItemColor = (name: string) => {
    let category = getCategory(name)
    return categoryColors[category as keyof typeof categoryColors]
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

