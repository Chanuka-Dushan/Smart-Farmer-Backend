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
import Swal from 'sweetalert2'

interface User {
  id: number
  firstname: string
  lastname: string
  email: string
  phone_number: string | null
  address: string | null
  user_type: 'app_user' | 'seller'
  is_banned: boolean
  is_deleted: boolean
  created_at: string
}

interface Seller {
  id: number
  business_name: string
  owner_firstname: string
  owner_lastname: string
  email: string
  phone_number: string | null
  business_address: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
}

interface Seller {
  id: number
  business_name: string
  owner_firstname: string
  owner_lastname: string
  email: string
  phone_number: string | null
  business_address: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
}

interface UserStats {
  total_users: number
  active_users: number
  banned_users: number
  deleted_users: number
}

function UsersManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [stats, setStats] = useState<UserStats>({
    total_users: 0,
    active_users: 0,
    banned_users: 0,
    deleted_users: 0
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
      const token = localStorage.getItem('authToken')
      const headers = {
        'Authorization': `Bearer ${token}`
      }

      // Fetch app users
      const usersResponse = await fetch(`/api/admin/users?limit=100&search=${searchQuery}`, {
        headers,
      })
      
      // Fetch sellers
      const sellersResponse = await fetch(`/api/admin/sellers?limit=100&search=${searchQuery}`, {
        headers,
      })
      
      if (usersResponse.ok && sellersResponse.ok) {
        const usersData = await usersResponse.json()
        const sellersData = await sellersResponse.json()
        
        // Transform app users to include user_type
        const transformedUsers: User[] = usersData.map((user: any) => ({
          ...user,
          user_type: 'app_user' as const
        }))
        
        // Transform sellers to match User interface
        const transformedSellers: User[] = sellersData.map((seller: Seller) => ({
          id: seller.id,
          firstname: seller.owner_firstname,
          lastname: seller.owner_lastname,
          email: seller.email,
          phone_number: seller.phone_number,
          address: seller.business_address,
          user_type: 'seller' as const,
          is_banned: !seller.is_active,
          is_deleted: false,
          created_at: seller.created_at
        }))
        
        // Combine both arrays
        const combinedUsers = [...transformedUsers, ...transformedSellers]
        setUsers(combinedUsers)
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

  const handleBanUser = async (userId: number, currentBanStatus: boolean) => {
    try {
      // Find the user to determine the type
      const user = users.find(u => u.id === userId)
      if (!user) {
        toast({
          title: "Error",
          description: "User not found",
          variant: "destructive"
        })
        return
      }

      const token = localStorage.getItem('authToken')
      let endpoint: string
      let action: string
      
      if (user.user_type === 'seller') {
        // For sellers, use activate/deactivate endpoint
        endpoint = `/api/admin/sellers/${userId}/activate?is_active=${currentBanStatus}`
        action = currentBanStatus ? 'deactivated' : 'activated'
      } else {
        // For app users, use ban/unban endpoint
        endpoint = `/api/admin/users/${userId}/ban?is_banned=${!currentBanStatus}`
        action = !currentBanStatus ? 'banned' : 'unbanned'
      }

      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        toast({
          title: "Success",
          description: `User ${action} successfully`
        })
        fetchUsers()
        fetchStats()
      } else {
        toast({
          title: "Error",
          description: "Failed to update user status",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to ban/unban user:', error)
      toast({
        title: "Error",
        description: "Failed to update user status",
        variant: "destructive"
      })
    }
  }

  const handleDeleteUser = async (userId: number, permanent: boolean = false) => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: permanent 
        ? "This action cannot be undone. The user will be permanently deleted." 
        : "The user will be soft deleted and can be restored.",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: permanent ? 'Yes, permanently delete!' : 'Yes, delete it!'
    })

    if (!result.isConfirmed) {
      return
    }

    try {
      // Find the user to determine the type
      const user = users.find(u => u.id === userId)
      if (!user) {
        toast({
          title: "Error",
          description: "User not found",
          variant: "destructive"
        })
        return
      }

      const token = localStorage.getItem('authToken')
      let endpoint: string
      
      if (user.user_type === 'seller') {
        endpoint = `/api/admin/sellers/${userId}${permanent ? '?permanent=true' : ''}`
      } else {
        endpoint = `/api/admin/users/${userId}?permanent=${permanent}`
      }

      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        toast({
          title: "Success",
          description: `User ${permanent ? 'permanently deleted' : 'soft deleted'} successfully`
        })
        fetchUsers()
        fetchStats()
      } else {
        toast({
          title: "Error",
          description: "Failed to delete user",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to delete user:', error)
      toast({
        title: "Error",
        description: "Failed to delete user",
        variant: "destructive"
      })
    }
  }

  const openEditDialog = (user: User) => {
    setSelectedUser(user)
    setEditForm({
      firstname: user.firstname,
      lastname: user.lastname,
      email: user.email,
      phone_number: user.phone_number || "",
      address: user.address || ""
    })
    setEditDialogOpen(true)
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return

    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`/api/admin/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editForm)
      })
      
      if (response.ok) {
        toast({
          title: "Success",
          description: "User updated successfully"
        })
        setEditDialogOpen(false)
        fetchUsers()
      } else {
        const error = await response.json()
        toast({
          title: "Error",
          description: error.detail || "Failed to update user",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to update user:', error)
      toast({
        title: "Error",
        description: "Failed to update user",
        variant: "destructive"
      })
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
            <h2 className="text-3xl font-bold tracking-tight">Users Management</h2>
            <p className="text-muted-foreground">Manage mobile app users and permissions</p>
          </div>
          <Button 
            onClick={() => { fetchUsers(); fetchStats(); }}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                {stats.total_users}
              </div>
              <p className="text-xs text-muted-foreground mt-1">All registered users</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                {stats.active_users}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Not banned or deleted</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Banned Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                {stats.banned_users}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Currently banned</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Deleted Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold bg-gradient-to-r from-gray-600 to-slate-600 bg-clip-text text-transparent">
                {stats.deleted_users}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Soft deleted</p>
            </CardContent>
          </Card>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <UsersIcon className="h-5 w-5 text-green-600" />
                  All Users
                </CardTitle>
                <CardDescription>A list of all mobile app users</CardDescription>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Search users..." 
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
              <div className="text-center py-8">Loading...</div>
            ) : users.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No users found</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-sm font-semibold">
                            {user.firstname?.[0] || ''}{user.lastname?.[0] || ''}
                          </div>
                          {user.firstname} {user.lastname}
                        </div>
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          user.user_type === 'seller' 
                            ? "border-emerald-500 text-emerald-600 bg-emerald-50" 
                            : "border-blue-500 text-blue-600 bg-blue-50"
                        }>
                          {user.user_type === 'app_user' ? 'BUYER' : 'SELLER'}
                        </Badge>
                      </TableCell>
                      <TableCell>{user.phone_number || '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {user.is_banned && (
                            <Badge variant="destructive">Banned</Badge>
                          )}
                          {user.is_deleted && (
                            <Badge variant="secondary">Deleted</Badge>
                          )}
                          {!user.is_banned && !user.is_deleted && (
                            <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                              Active
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(user)}>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit User
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleBanUser(user.id, user.is_banned)}>
                              <Ban className="h-4 w-4 mr-2" />
                              {user.is_banned ? 'Unban User' : 'Ban User'}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteUser(user.id, false)}
                              className="text-orange-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Soft Delete
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDeleteUser(user.id, true)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Permanent Delete
                            </DropdownMenuItem>
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

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user information. Changes will be saved immediately.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstname">First Name</Label>
                <Input
                  id="firstname"
                  value={editForm.firstname}
                  onChange={(e) => setEditForm({ ...editForm, firstname: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastname">Last Name</Label>
                <Input
                  id="lastname"
                  value={editForm.lastname}
                  onChange={(e) => setEditForm({ ...editForm, lastname: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                value={editForm.phone_number}
                onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={editForm.address}
                onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateUser} className="bg-gradient-to-r from-green-500 to-emerald-600">
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
