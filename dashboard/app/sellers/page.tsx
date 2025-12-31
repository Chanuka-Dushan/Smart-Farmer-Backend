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
import { Store, UserPlus, Search, MoreVertical, CheckCircle, XCircle } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useState, useEffect } from "react"

interface Seller {
  id: number
  business_name: string
  owner_firstname: string
  owner_lastname: string
  email: string
  phone_number?: string
  business_address?: string
  business_description?: string
  is_verified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function SellersPage() {
  const [sellers, setSellers] = useState<Seller[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    fetchSellers()
  }, [])

  const fetchSellers = async () => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch('/api/admin/sellers', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setSellers(data)
      }
    } catch (error) {
      console.error('Failed to fetch sellers:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleVerification = async (sellerId: number, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`/api/admin/sellers/${sellerId}/verify`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_verified: !currentStatus }),
      })
      
      if (response.ok) {
        fetchSellers() // Refresh the list
      }
    } catch (error) {
      console.error('Failed to update seller verification:', error)
    }
  }

  const toggleActivation = async (sellerId: number, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`/api/admin/sellers/${sellerId}/activate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: !currentStatus }),
      })
      
      if (response.ok) {
        fetchSellers() // Refresh the list
      }
    } catch (error) {
      console.error('Failed to update seller activation:', error)
    }
  }

  const filteredSellers = sellers.filter(seller =>
    seller.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    seller.owner_firstname.toLowerCase().includes(searchTerm.toLowerCase()) ||
    seller.owner_lastname.toLowerCase().includes(searchTerm.toLowerCase()) ||
    seller.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading sellers...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Sellers</h2>
            <p className="text-muted-foreground">Manage seller accounts and verifications</p>
          </div>
          <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
            <UserPlus className="h-4 w-4 mr-2" />
            Add Seller
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Sellers</CardTitle>
              <div className="text-2xl font-bold">{sellers.length}</div>
            </CardHeader>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Sellers</CardTitle>
              <div className="text-2xl font-bold">{sellers.filter(s => s.is_active).length}</div>
            </CardHeader>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Verified Sellers</CardTitle>
              <div className="text-2xl font-bold">{sellers.filter(s => s.is_verified).length}</div>
            </CardHeader>
          </Card>
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Pending Verification</CardTitle>
              <div className="text-2xl font-bold">{sellers.filter(s => !s.is_verified && s.is_active).length}</div>
            </CardHeader>
          </Card>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Seller Management</CardTitle>
            <CardDescription>View and manage all seller accounts</CardDescription>
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search sellers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Business Name</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Verified</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSellers.map((seller) => (
                  <TableRow key={seller.id}>
                    <TableCell className="font-medium">{seller.business_name}</TableCell>
                    <TableCell>{`${seller.owner_firstname} ${seller.owner_lastname}`}</TableCell>
                    <TableCell>{seller.email}</TableCell>
                    <TableCell>
                      <Badge variant={seller.is_active ? "default" : "secondary"}>
                        {seller.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={seller.is_verified ? "default" : "outline"}>
                        {seller.is_verified ? "Verified" : "Pending"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => toggleVerification(seller.id, seller.is_verified)}>
                            {seller.is_verified ? (
                              <>
                                <XCircle className="mr-2 h-4 w-4" />
                                Unverify
                              </>
                            ) : (
                              <>
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Verify
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => toggleActivation(seller.id, seller.is_active)}>
                            {seller.is_active ? (
                              <>
                                <XCircle className="mr-2 h-4 w-4" />
                                Deactivate
                              </>
                            ) : (
                              <>
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Activate
                              </>
                            )}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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