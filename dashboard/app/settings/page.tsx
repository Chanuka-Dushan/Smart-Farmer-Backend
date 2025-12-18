"use client"

import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Settings as SettingsIcon, User, Bell, Shield, Palette, Globe } from "lucide-react"
import { useState } from "react"

export default function SettingsPage() {
  const [name, setName] = useState("Admin User")
  const [email, setEmail] = useState("admin@example.com")
  const [showThemeSettings, setShowThemeSettings] = useState(false)
  const [primaryColor, setPrimaryColor] = useState("#3b82f6")
  const [secondaryColor, setSecondaryColor] = useState("#8b5cf6")

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
          <p className="text-muted-foreground">Manage your account settings and preferences</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Settings Navigation */}
          <Card className="border-0 shadow-lg lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SettingsIcon className="h-5 w-5 text-blue-600" />
                Categories
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button 
                variant="default" 
                className="w-full justify-start"
                style={{
                  background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                }}
              >
                <User className="h-4 w-4 mr-2" />
                Profile
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                <Bell className="h-4 w-4 mr-2" />
                Notifications
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                <Shield className="h-4 w-4 mr-2" />
                Security
              </Button>
              <Button 
                variant={showThemeSettings ? "secondary" : "ghost"}
                className="w-full justify-start"
                onClick={() => setShowThemeSettings(!showThemeSettings)}
              >
                <Palette className="h-4 w-4 mr-2" />
                Appearance
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                <Globe className="h-4 w-4 mr-2" />
                Language & Region
              </Button>
            </CardContent>
          </Card>

          {/* Settings Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Settings */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your account profile information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-semibold">
                    A
                  </div>
                  <div>
                    <Button variant="outline" size="sm">Change Avatar</Button>
                    <p className="text-xs text-muted-foreground mt-1">JPG, PNG or GIF. Max 2MB</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Full Name</label>
                  <Input 
                    value={name} 
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name" 
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Email Address</label>
                  <Input 
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email" 
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Bio</label>
                  <textarea 
                    className="w-full min-h-[100px] px-3 py-2 rounded-md border border-input bg-background text-sm"
                    placeholder="Tell us about yourself..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
                    Save Changes
                  </Button>
                  <Button variant="outline">Cancel</Button>
                </div>
              </CardContent>
            </Card>

            {/* Notification Settings */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Choose what notifications you want to receive</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <p className="font-medium">Email Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive email about your account activity</p>
                  </div>
                  <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Enabled
                  </Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <p className="font-medium">Push Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive push notifications on your devices</p>
                  </div>
                  <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Enabled
                  </Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <p className="font-medium">SMS Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive text messages about important updates</p>
                  </div>
                  <Badge variant="secondary">Disabled</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Security Settings */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Security</CardTitle>
                <CardDescription>Manage your account security settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Current Password</label>
                  <Input type="password" placeholder="Enter current password" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">New Password</label>
                  <Input type="password" placeholder="Enter new password" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Confirm New Password</label>
                  <Input type="password" placeholder="Confirm new password" />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
                    Update Password
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Theme Customization */}
            {showThemeSettings && (
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle>Theme Customization</CardTitle>
                  <CardDescription>Customize your dashboard colors and appearance</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Primary Color</label>
                      <div className="flex gap-3 items-center">
                        <input 
                          type="color" 
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          className="h-12 w-20 rounded-md border cursor-pointer"
                        />
                        <Input 
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          placeholder="#3b82f6"
                          className="flex-1"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">Used for buttons and highlights</p>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Secondary Color</label>
                      <div className="flex gap-3 items-center">
                        <input 
                          type="color" 
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          className="h-12 w-20 rounded-md border cursor-pointer"
                        />
                        <Input 
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          placeholder="#8b5cf6"
                          className="flex-1"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">Used for gradients and accents</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-sm font-medium">Preview</label>
                    <div className="p-6 rounded-lg border bg-slate-50 dark:bg-slate-900 space-y-4">
                      <div className="flex gap-3">
                        <Button 
                          style={{
                            background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                          }}
                        >
                          Primary Button
                        </Button>
                        <Badge 
                          style={{
                            background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                          }}
                          className="text-white"
                        >
                          Badge
                        </Badge>
                      </div>
                      
                      <div 
                        className="h-20 rounded-lg flex items-center justify-center text-white font-semibold"
                        style={{
                          background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                        }}
                      >
                        Gradient Preview
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div 
                          className="h-16 rounded-lg"
                          style={{ backgroundColor: primaryColor }}
                        />
                        <div 
                          className="h-16 rounded-lg"
                          style={{ 
                            background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                          }}
                        />
                        <div 
                          className="h-16 rounded-lg"
                          style={{ backgroundColor: secondaryColor }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-sm font-medium">Preset Themes</label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <button
                        onClick={() => {
                          setPrimaryColor("#3b82f6")
                          setSecondaryColor("#8b5cf6")
                        }}
                        className="p-3 rounded-lg border hover:border-blue-500 transition-colors"
                      >
                        <div className="h-8 rounded bg-gradient-to-r from-blue-500 to-purple-600 mb-2" />
                        <p className="text-xs font-medium">Default</p>
                      </button>
                      <button
                        onClick={() => {
                          setPrimaryColor("#10b981")
                          setSecondaryColor("#059669")
                        }}
                        className="p-3 rounded-lg border hover:border-green-500 transition-colors"
                      >
                        <div className="h-8 rounded bg-gradient-to-r from-emerald-500 to-green-600 mb-2" />
                        <p className="text-xs font-medium">Green</p>
                      </button>
                      <button
                        onClick={() => {
                          setPrimaryColor("#f59e0b")
                          setSecondaryColor("#ef4444")
                        }}
                        className="p-3 rounded-lg border hover:border-orange-500 transition-colors"
                      >
                        <div className="h-8 rounded bg-gradient-to-r from-amber-500 to-red-500 mb-2" />
                        <p className="text-xs font-medium">Sunset</p>
                      </button>
                      <button
                        onClick={() => {
                          setPrimaryColor("#ec4899")
                          setSecondaryColor("#a855f7")
                        }}
                        className="p-3 rounded-lg border hover:border-pink-500 transition-colors"
                      >
                        <div className="h-8 rounded bg-gradient-to-r from-pink-500 to-purple-500 mb-2" />
                        <p className="text-xs font-medium">Pink</p>
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-4">
                    <Button 
                      style={{
                        background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
                      }}
                    >
                      Apply Theme
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => {
                        setPrimaryColor("#3b82f6")
                        setSecondaryColor("#8b5cf6")
                      }}
                    >
                      Reset to Default
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
