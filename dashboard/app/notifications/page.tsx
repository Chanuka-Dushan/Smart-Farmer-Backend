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

  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNotifications = async () => {
    try {
      const response = await fetch('/api/notifications')
      if (response.ok) {
        const data = await response.json()
        setNotifications(data)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendNotification = async () => {
    if (!formData.title.trim() || !formData.message.trim()) {
      alert('Please fill in all required fields')
      return
    }

    setSending(true)
    try {
      const payload: any = {
        title: formData.title,
        message: formData.message,
        user_type: formData.user_type,
      }

      if (formData.user_type !== 'all' && formData.target_user_id) {
        payload.target_user_id = parseInt(formData.target_user_id)
      }

      const response = await fetch('/api/notifications/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        alert('Notification sent successfully!')
        setIsDialogOpen(false)
        setFormData({
          title: '',
          message: '',
          user_type: 'all',
          target_user_id: '',
        })
        fetchNotifications()
      } else {
        const error = await response.json()
        alert(`Failed to send notification: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to send notification:', error)
      alert('Failed to send notification')
    } finally {
      setSending(false)
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
                    Title
                  </Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="col-span-3"
                    placeholder="Notification title"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="message" className="text-right">
                    Message
                  </Label>
                  <Textarea
                    id="message"
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="col-span-3"
                    placeholder="Notification message"
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="user_type" className="text-right">
                    Target
                  </Label>
                  <Select value={formData.user_type} onValueChange={(value) => setFormData({ ...formData, user_type: value })}>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select target audience" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Users & Sellers</SelectItem>
                      <SelectItem value="app_user">All App Users</SelectItem>
                      <SelectItem value="seller">All Sellers</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {(formData.user_type === 'app_user' || formData.user_type === 'seller') && (
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="target_user_id" className="text-right">
                      User ID
                    </Label>
                    <Input
                      id="target_user_id"
                      type="number"
                      value={formData.target_user_id}
                      onChange={(e) => setFormData({ ...formData, target_user_id: e.target.value })}
                      className="col-span-3"
                      placeholder="Specific user ID (optional)"
                    />
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button type="submit" onClick={handleSendNotification} disabled={sending}>
                  {sending ? (
                    <>Sending...</>
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
            <CardTitle>Notification History</CardTitle>
            <CardDescription>View all sent and pending notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Sent At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {notifications.map((notification) => (
                  <TableRow key={notification.id}>
                    <TableCell className="font-medium">{notification.title}</TableCell>
                    <TableCell className="max-w-xs truncate">{notification.message}</TableCell>
                    <TableCell>
                      {notification.user_type === 'all' ? 'All Users & Sellers' :
                       notification.user_type === 'app_user' ? 'App Users' : 'Sellers'}
                      {notification.target_user_id && ` (ID: ${notification.target_user_id})`}
                    </TableCell>
                    <TableCell>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        notification.is_sent
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {notification.is_sent ? 'Sent' : 'Pending'}
                      </span>
                    </TableCell>
                    <TableCell>
                      {notification.sent_at ? new Date(notification.sent_at).toLocaleString() : 'Not sent'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}