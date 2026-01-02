"use client"

import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Bell, Send, Plus } from "lucide-react"
import { useState, useEffect } from "react"

interface Notification {
  id: number
  title: string
  message: string
  user_type: string
  target_user_id?: number
  sent_by: number
  is_sent: boolean
  sent_at?: string
  created_at: string
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [sending, setSending] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    message: '',
    user_type: 'all',
    target_user_id: '',
  })
  const [errors, setErrors] = useState<{[key: string]: string}>({})

  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/notifications`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setNotifications(data)
      } else {
        const errorData = await response.json()
        console.error('Failed to fetch notifications:', errorData)
        alert(`Failed to load notifications: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
      alert('Failed to load notifications. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const validateForm = (): boolean => {
    const newErrors: {[key: string]: string} = {}

    // Validate title
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    } else if (formData.title.trim().length < 3) {
      newErrors.title = 'Title must be at least 3 characters long'
    } else if (formData.title.trim().length > 100) {
      newErrors.title = 'Title must be less than 100 characters'
    }

    // Validate message
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required'
    } else if (formData.message.trim().length < 10) {
      newErrors.message = 'Message must be at least 10 characters long'
    } else if (formData.message.trim().length > 500) {
      newErrors.message = 'Message must be less than 500 characters'
    }

    // Validate target user ID if specific user type is selected
    if ((formData.user_type === 'app_user' || formData.user_type === 'seller') && formData.target_user_id) {
      const userId = parseInt(formData.target_user_id)
      if (isNaN(userId) || userId <= 0) {
        newErrors.target_user_id = 'Please enter a valid user ID'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSendNotification = async () => {
    if (!validateForm()) {
      return
    }

    setSending(true)
    try {
      const payload: any = {
        title: formData.title.trim(),
        message: formData.message.trim(),
        user_type: formData.user_type,
      }

      if (formData.user_type !== 'all' && formData.target_user_id.trim()) {
        payload.target_user_id = parseInt(formData.target_user_id.trim())
      }

      const token = localStorage.getItem('token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/notifications/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload),
      })

      const responseData = await response.json()

      if (response.ok) {
        alert(`✅ ${responseData.message || 'Notification sent successfully!'}`)
        setIsDialogOpen(false)
        setFormData({
          title: '',
          message: '',
          user_type: 'all',
          target_user_id: '',
        })
        setErrors({})
        fetchNotifications()
      } else {
        const errorMessage = responseData.detail || responseData.message || 'Unknown error occurred'
        alert(`❌ Failed to send notification: ${errorMessage}`)
      }
    } catch (error) {
      console.error('Failed to send notification:', error)
      alert('❌ Failed to send notification. Please check your connection and try again.')
    } finally {
      setSending(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString()
    } catch {
      return dateString
    }
  }

  const getStatusBadge = (notification: Notification) => {
    if (notification.is_sent) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ✅ Sent
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          ⏳ Pending
        </span>
      )
    }
  }

  const getUserTypeLabel = (userType: string) => {
    switch (userType) {
      case 'all':
        return 'All Users & Sellers'
      case 'app_user':
        return 'App Users'
      case 'seller':
        return 'Sellers'
      default:
        return userType
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading notifications...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Notifications</h2>
            <p className="text-muted-foreground">Send notifications to users and sellers</p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
                <Plus className="h-4 w-4 mr-2" />
                Send Notification
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Send New Notification</DialogTitle>
                <DialogDescription>
                  Send a push notification to users or sellers through the mobile app.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="title" className="text-right">
                    Title *
                  </Label>
                  <div className="col-span-3">
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      className={`w-full ${errors.title ? 'border-red-500' : ''}`}
                      placeholder="Enter notification title"
                      maxLength={100}
                    />
                    {errors.title && (
                      <p className="text-sm text-red-600 mt-1">{errors.title}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      {formData.title.length}/100 characters
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label htmlFor="message" className="text-right mt-2">
                    Message *
                  </Label>
                  <div className="col-span-3">
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleInputChange('message', e.target.value)}
                      className={`w-full ${errors.message ? 'border-red-500' : ''}`}
                      placeholder="Enter notification message"
                      rows={4}
                      maxLength={500}
                    />
                    {errors.message && (
                      <p className="text-sm text-red-600 mt-1">{errors.message}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      {formData.message.length}/500 characters
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="user_type" className="text-right">
                    Target Audience *
                  </Label>
                  <div className="col-span-3">
                    <Select 
                      value={formData.user_type} 
                      onValueChange={(value) => handleInputChange('user_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select target audience" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">🌍 All Users & Sellers</SelectItem>
                        <SelectItem value="app_user">👤 App Users Only</SelectItem>
                        <SelectItem value="seller">🏪 Sellers Only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {(formData.user_type === 'app_user' || formData.user_type === 'seller') && (
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="target_user_id" className="text-right">
                      User ID
                    </Label>
                    <div className="col-span-3">
                      <Input
                        id="target_user_id"
                        type="number"
                        value={formData.target_user_id}
                        onChange={(e) => handleInputChange('target_user_id', e.target.value)}
                        className={`w-full ${errors.target_user_id ? 'border-red-500' : ''}`}
                        placeholder="Enter specific user ID (optional)"
                        min="1"
                      />
                      {errors.target_user_id && (
                        <p className="text-sm text-red-600 mt-1">{errors.target_user_id}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        Leave empty to send to all {formData.user_type === 'app_user' ? 'app users' : 'sellers'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              
              <DialogFooter>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    setIsDialogOpen(false)
                    setErrors({})
                  }}
                  disabled={sending}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleSendNotification} 
                  disabled={sending}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  {sending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Send Notification
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Notifications</CardTitle>
              <div className="text-2xl font-bold">{notifications.length}</div>
            </CardHeader>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Sent Notifications</CardTitle>
              <div className="text-2xl font-bold">{notifications.filter(n => n.is_sent).length}</div>
            </CardHeader>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Pending Notifications</CardTitle>
              <div className="text-2xl font-bold">{notifications.filter(n => !n.is_sent).length}</div>
            </CardHeader>
          </Card>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Notification History</CardTitle>
                <CardDescription>View all sent and pending notifications</CardDescription>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchNotifications}
                disabled={loading}
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                ) : (
                  "Refresh"
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {notifications.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications yet</h3>
                <p className="text-gray-500 mb-4">Start by sending your first notification to users.</p>
                <Button onClick={() => setIsDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Send First Notification
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[150px]">Title</TableHead>
                      <TableHead className="min-w-[200px]">Message</TableHead>
                      <TableHead className="min-w-[120px]">Target Audience</TableHead>
                      <TableHead className="min-w-[100px]">Status</TableHead>
                      <TableHead className="min-w-[150px]">Created At</TableHead>
                      <TableHead className="min-w-[150px]">Sent At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {notifications.map((notification) => (
                      <TableRow key={notification.id} className="hover:bg-gray-50">
                        <TableCell className="font-medium">
                          <div className="max-w-[150px]">
                            <div className="truncate" title={notification.title}>
                              {notification.title}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-[200px]">
                            <div 
                              className="truncate text-sm text-gray-600" 
                              title={notification.message}
                            >
                              {notification.message}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <span className="text-sm font-medium">
                              {getUserTypeLabel(notification.user_type)}
                            </span>
                            {notification.target_user_id && (
                              <span className="text-xs text-gray-500">
                                User ID: {notification.target_user_id}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(notification)}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {formatDate(notification.created_at)}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {notification.sent_at ? formatDate(notification.sent_at) : (
                            <span className="text-gray-400 italic">Not sent yet</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}