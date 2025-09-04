"use client"

import React from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart"
import { BarChart, Bar, LineChart, Line, XAxis, YAxis } from "recharts"

interface StatItem {
  group: string
  lastDuration: number
  avgDuration: number
  success: number
  failure: number
  outputs: Record<string, number>
  date: string
}

interface StatsResponse {
  data: StatItem[]
}

export default function StatsPage() {
  const [timeWindow, setTimeWindow] = React.useState(1)
  const [stats, setStats] = React.useState<StatItem[]>([])
  const [chartType, setChartType] = React.useState<"bar" | "line">("bar")
  const [dimension, setDimension] = React.useState<"group" | "date">(
    "group"
  )

  const fetchStats = React.useCallback(async () => {
    const res = await fetch(`/api/stats?window=${timeWindow}`)
    if (res.ok) {
      const json: StatsResponse = await res.json()
      setStats(json.data)
    }
  }, [timeWindow])

  React.useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const handleExport = async (format: "csv" | "json") => {
    const res = await fetch(
      `/api/stats/export?window=${timeWindow}&format=${format}`
    )
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `stats.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const chartData = React.useMemo(() => {
    const map: Record<string, { total: number; count: number }> = {}
    if (dimension === "group") {
      stats.forEach((s) => {
        const entry = map[s.group] || { total: 0, count: 0 }
        entry.total += s.avgDuration
        entry.count += 1
        map[s.group] = entry
      })
    } else {
      stats.forEach((s) => {
        const entry = map[s.date] || { total: 0, count: 0 }
        entry.total += s.avgDuration
        entry.count += 1
        map[s.date] = entry
      })
    }
    return Object.entries(map).map(([label, { total, count }]) => ({
      label,
      value: total / count,
    }))
  }, [stats, dimension])

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="window">Time Window</label>
        <select
          id="window"
          value={timeWindow}
          onChange={(e) => setTimeWindow(Number(e.target.value))}
          className="border p-1"
        >
          <option value={1}>1</option>
          <option value={7}>7</option>
          <option value={30}>30</option>
        </select>
        <Button onClick={() => setChartType(chartType === "bar" ? "line" : "bar")}>
          {chartType === "bar" ? "Line" : "Bar"}
        </Button>
        <Button
          onClick={() =>
            setDimension(dimension === "group" ? "date" : "group")
          }
        >
          {dimension === "group" ? "By Date" : "By Group"}
        </Button>
        <Button onClick={() => handleExport("csv")}>Export CSV</Button>
        <Button onClick={() => handleExport("json")}>Export JSON</Button>
      </div>
      <ChartContainer
        config={{ value: { label: "Avg Duration", color: "hsl(var(--chart-1))" } }}
      >
        {chartType === "bar" ? (
          <BarChart data={chartData}>
            <XAxis dataKey="label" />
            <YAxis />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="value" fill="var(--color-value)" />
            <ChartLegend content={<ChartLegendContent />} />
          </BarChart>
        ) : (
          <LineChart data={chartData}>
            <XAxis dataKey="label" />
            <YAxis />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line type="monotone" dataKey="value" stroke="var(--color-value)" />
            <ChartLegend content={<ChartLegendContent />} />
          </LineChart>
        )}
      </ChartContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>配置組</TableHead>
            <TableHead>最近一次耗時</TableHead>
            <TableHead>平均耗時</TableHead>
            <TableHead>成功/失敗次數</TableHead>
            <TableHead>產物分類與數量</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {stats.map((s) => (
            <TableRow key={s.group + s.date}>
              <TableCell>{s.group}</TableCell>
              <TableCell>{s.lastDuration}</TableCell>
              <TableCell>{s.avgDuration}</TableCell>
              <TableCell>
                {s.success}/{s.failure}
              </TableCell>
              <TableCell>
                {Object.entries(s.outputs)
                  .map(([k, v]) => `${k}:${v}`)
                  .join(", ")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

