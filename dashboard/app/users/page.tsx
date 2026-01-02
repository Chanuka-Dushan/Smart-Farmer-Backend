"use client"

import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Users as UsersIcon, Search, MoreVertical, Ban, Trash2, Edit, RefreshCw } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { useEffect, useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { ProtectedRoute } from "@/components/ProtectedRoute"

interface User {
  id: number
  firstname: string
  lastname: string
  email: string
  phone_number: string | null
  address: string | null
  user_type: 'buyer' | 'seller'
  is_banned: boolean
  is_deleted: boolean
  created_at: string
}

interface UserStats {
  total_users: number
  active_users: number
  banned_users: number
  deleted_users: number
  buyers_count: number
  sellers_count: number
}

function UsersManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [stats, setStats] = useState<UserStats>({
    total_users: 0,
    active_users: 0,
    banned_users: 0,
    deleted_users: 0,
    buyers_count: 0,
    sellers_count: 0
  })
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [editForm, setEditForm] = useState({
    firstname: "",
    lastname: "",
    email: "",
    phone_number: "",
    address: ""
  })
  const { toast } = useToast()

  useEffect(() => {
    fetchUsers()
    fetchStats()
  }, [])

  const fetchUsers = async () => {
    try {
      // Ensure we're on the client side
      if (typeof window === 'undefined') return
      
      const token = localStorage.getItem('authToken')
      const response = await fetch(`/api/admin/users?limit=100&search=${searchQuery}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setUsers(data)
      } else {
        toast({
          title: "Error",
          description: "Failed to fetch users",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast({
        title: "Error",
        description: "Failed to fetch users",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      // Ensure we're on the client side
      if (typeof window === 'undefined') return
      
      const token = localStorage.getItem('authToken')
      const response = await fetch('/api/admin/users/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const handleSearch = () => {
    setLoading(true)
    fetchUsers()
  }

  const handleBanUser = async (user: User) => {
    try {
      if (typeof window === 'undefined') return
      
      const token = localStorage.getItem('authToken')
      const endpoint = user.user_type === 'seller' 
        ? `/api/admin/sellers/${user.id}/activate` 
        : `/api/admin/users/${user.id}/ban`
      
      const response = await fetch(`${endpoint}?${user.user_type === 'seller' ? 'is_active' : 'is_banned'}=${user.user_type === 'seller' ? user.is_banned : !user.is_banned}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        toast({
          title: "Success",
          description: `User status updated successfully`
        })
        fetchUsers()
        fetchStats()
      }
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  const handleDeleteUser = async (user: User, permanent: boolean = false) => {
    if (!confirm(`Are you sure?`)) return

    try {
      if (typeof window === 'undefined') return
      
      const token = localStorage.getItem('authToken')
      const endpoint = user.user_type === 'seller' 
        ? `/api/admin/sellers/${user.id}` 
        : `/api/admin/users/${user.id}?permanent=${permanent}`
        
      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        toast({ title: "Success", description: "User deleted" })
        fetchUsers()
        fetchStats()
      }
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return dateString
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Real-time User Management</h2>
            <p className="text-muted-foreground">Connected to live production database</p>
          </div>
          <Button onClick={() => { fetchUsers(); fetchStats(); }} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total (Buyers + Sellers)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                {stats.total_users}
              </div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Buyers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{stats.buyers_count}</div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Sellers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-600">{stats.sellers_count}</div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Now</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">{stats.active_users}</div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <UsersIcon className="h-5 w-5 text-green-600" />
                Live User List
              </CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Search live data..." 
                  className="pl-9" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 italic uppercase tracking-widest animate-pulse">Fetching Real-time data...</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Account Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={`${user.user_type}-${user.id}`}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-3">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white text-xs font-bold ${user.user_type === 'seller' ? 'bg-emerald-500' : 'bg-blue-500'}`}>
                            {user.firstname?.[0] || ''}{user.lastname?.[0] || ''}
                          </div>
                          {user.firstname} {user.lastname}
                        </div>
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={user.user_type === 'seller' ? "border-emerald-500 text-emerald-600" : "border-blue-500 text-blue-600"}>
                          {user.user_type?.toUpperCase() || 'UNKNOWN'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.is_banned ? <Badge variant="destructive">Banned</Badge> : <Badge className="bg-green-100 text-green-700">Active</Badge>}
                      </TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleBanUser(user)}>{user.is_banned ? 'Unban' : 'Ban'}</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDeleteUser(user, true)} className="text-red-600">Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

export default function UsersPage() {
  return (
    <ProtectedRoute>
      <UsersManagement />
    </ProtectedRoute>
  )
}
