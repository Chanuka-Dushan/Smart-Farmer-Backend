"use client"

import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, TrendingUp, Users, DollarSign, Activity, ArrowUpRight, ArrowDownRight } from "lucide-react"
import { AreaChart, Area, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const revenueData = [
  { month: 'Jan', revenue: 4200 },
  { month: 'Feb', revenue: 3800 },
  { month: 'Mar', revenue: 5100 },
  { month: 'Apr', revenue: 4600 },
  { month: 'May', revenue: 5800 },
  { month: 'Jun', revenue: 6200 },
]

const pageViewsData = [
  { day: 'Mon', views: 2400 },
  { day: 'Tue', views: 1398 },
  { day: 'Wed', views: 9800 },
  { day: 'Thu', views: 3908 },
  { day: 'Fri', views: 4800 },
  { day: 'Sat', views: 3800 },
  { day: 'Sun', views: 4300 },
]

const userGrowthData = [
  { month: 'Jan', users: 180 },
  { month: 'Feb', users: 220 },
  { month: 'Mar', users: 280 },
  { month: 'Apr', users: 320 },
  { month: 'May', users: 380 },
  { month: 'Jun', users: 450 },
]

export default function AnalyticsPage() {
  const metrics = [
    { title: "Total Revenue", value: "$45,231.89", change: "+20.1%", trend: "up", icon: DollarSign },
    { title: "Page Views", value: "1.2M", change: "+15.3%", trend: "up", icon: Activity },
    { title: "Conversion Rate", value: "3.24%", change: "+2.4%", trend: "up", icon: TrendingUp },
    { title: "Bounce Rate", value: "42.3%", change: "-5.2%", trend: "down", icon: Users },
  ]

  const topPages = [
    { page: "/dashboard", views: "45.2K", change: "+12.3%" },
    { page: "/products", views: "32.1K", change: "+8.7%" },
    { page: "/users", views: "28.5K", change: "+15.2%" },
    { page: "/settings", views: "18.9K", change: "+5.1%" },
  ]

  const trafficSources = [
    { source: "Direct", visitors: "12.5K", percentage: "35%" },
    { source: "Organic Search", visitors: "10.2K", percentage: "29%" },
    { source: "Social Media", visitors: "8.1K", percentage: "23%" },
    { source: "Referral", visitors: "4.6K", percentage: "13%" },
  ]

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
          <p className="text-muted-foreground">Track your performance and user engagement</p>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon
            const TrendIcon = metric.trend === "up" ? ArrowUpRight : ArrowDownRight
            return (
              <Card key={metric.title} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.title}
                  </CardTitle>
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {metric.value}
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <TrendIcon className={`h-4 w-4 ${metric.trend === "up" ? "text-green-600" : "text-red-600"}`} />
                    <span className={`text-sm font-medium ${metric.trend === "up" ? "text-green-600" : "text-red-600"}`}>
                      {metric.change}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">vs last month</span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Revenue Chart */}
          <Card className="border-0 shadow-lg lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                Revenue Over Time
              </CardTitle>
              <CardDescription>Monthly revenue for the past 6 months</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={revenueData}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
                  <XAxis dataKey="month" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorRevenue)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Page Views Chart */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Page Views Trend</CardTitle>
              <CardDescription>Daily page views for the past week</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={pageViewsData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
                  <XAxis dataKey="day" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="views" 
                    stroke="#8b5cf6" 
                    strokeWidth={3}
                    dot={{ fill: '#8b5cf6', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* User Growth Chart */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>User Growth</CardTitle>
              <CardDescription>New users registered each month</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={userGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
                  <XAxis dataKey="month" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar dataKey="users" fill="url(#colorBar)" radius={[8, 8, 0, 0]} />
                  <defs>
                    <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.9}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.7}/>
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top Pages */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Top Pages</CardTitle>
              <CardDescription>Most visited pages this month</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topPages.map((page, index) => (
                  <div key={page.page} className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{page.page}</p>
                      <p className="text-sm text-muted-foreground">{page.views} views</p>
                    </div>
                    <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      {page.change}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Traffic Sources */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Traffic Sources</CardTitle>
              <CardDescription>Where your visitors come from</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trafficSources.map((source) => (
                  <div key={source.source} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{source.source}</span>
                      <span className="text-muted-foreground">{source.visitors}</span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all"
                        style={{ width: source.percentage }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">{source.percentage} of total traffic</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
