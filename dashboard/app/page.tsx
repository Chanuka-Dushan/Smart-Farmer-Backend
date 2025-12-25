"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Sprout, Smartphone, TrendingUp, Users, Shield, Zap, Download, ArrowRight, Moon, Sun, Leaf, BarChart, Bell } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import Image from "next/image"

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/admin')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const features = [
    {
      icon: Sprout,
      title: "Smart Crop Management",
      description: "Monitor and manage your crops with AI-powered insights and real-time recommendations",
      color: "from-green-500 to-emerald-600"
    },
    {
      icon: TrendingUp,
      title: "Yield Optimization",
      description: "Maximize your harvest with data-driven farming techniques and predictive analytics",
      color: "from-blue-500 to-cyan-600"
    },
    {
      icon: Bell,
      title: "Smart Notifications",
      description: "Get instant alerts about weather changes, irrigation needs, and crop health status",
      color: "from-purple-500 to-pink-600"
    },
    {
      icon: BarChart,
      title: "Analytics Dashboard",
      description: "Track your farm's performance with detailed reports and visual insights",
      color: "from-orange-500 to-red-600"
    },
    {
      icon: Users,
      title: "Community Support",
      description: "Connect with fellow farmers and agricultural experts in your region",
      color: "from-teal-500 to-green-600"
    },
    {
      icon: Shield,
      title: "Secure & Reliable",
      description: "Your data is protected with enterprise-grade security and cloud backup",
      color: "from-indigo-500 to-purple-600"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 overflow-hidden">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-300 dark:bg-green-900 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-emerald-300 dark:bg-emerald-900 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-teal-300 dark:bg-teal-900 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Navigation */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-500 ${
        scrolled ? "bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl shadow-2xl border-b border-green-100 dark:border-gray-800" : "bg-transparent"
      }`}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110">
                <Sprout className="h-7 w-7 text-white animate-pulse" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Smart Farmer
              </span>
            </div>
            <div className="flex items-center gap-4">
              {mounted && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                  className="rounded-full hover:bg-green-100 dark:hover:bg-gray-800 transition-all duration-300"
                >
                  {theme === "dark" ? (
                    <Sun className="h-5 w-5 text-yellow-500 animate-spin-slow" />
                  ) : (
                    <Moon className="h-5 w-5 text-gray-700" />
                  )}
                </Button>
              )}
              <Link href="/admin">
                <Button variant="ghost" className="text-gray-600 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400 transition-all duration-300">
                  Admin Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 relative">
        <div className="container mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="space-y-8 animate-fade-in-up">
              <div className="inline-block animate-bounce-slow">
                <div className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 text-green-700 dark:text-green-400 text-sm font-semibold shadow-lg">
                  <Zap className="h-4 w-4 animate-pulse" />
                  <span>Revolutionizing Agriculture with AI</span>
                </div>
              </div>
              
              <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold leading-tight">
                <span className="bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 bg-clip-text text-transparent animate-gradient">
                  Farm Smarter,
                </span>
                <br />
                <span className="text-gray-900 dark:text-white inline-block animate-fade-in">
                  Grow Better
                </span>
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 leading-relaxed animate-fade-in-up animation-delay-200">
                Transform your farming with cutting-edge technology. Monitor crops, optimize yields, 
                and connect with a community of modern farmers.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 pt-4 animate-fade-in-up animation-delay-400">
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-10 py-7 text-lg rounded-2xl shadow-2xl hover:shadow-green-500/50 transition-all duration-500 hover:-translate-y-2 hover:scale-105 group"
                >
                  <Download className="h-6 w-6 mr-2 group-hover:animate-bounce" />
                  Download for Android
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-6 pt-8 animate-fade-in-up animation-delay-600">
                {[
                  { value: "10K+", label: "Active Farmers", icon: Users },
                  { value: "50K+", label: "Acres Managed", icon: Leaf },
                  { value: "95%", label: "Satisfaction", icon: TrendingUp }
                ].map((stat, index) => (
                  <div key={index} className="text-center group cursor-pointer">
                    <div className="flex justify-center mb-2">
                      <stat.icon className="h-6 w-6 text-green-600 dark:text-green-400 group-hover:scale-125 transition-transform duration-300" />
                    </div>
                    <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent group-hover:scale-110 transition-transform duration-300">
                      {stat.value}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right - Mobile Mockup */}
            <div className="relative lg:block animate-fade-in-right animation-delay-800">
              <div className="relative mx-auto max-w-xs">
                {/* Floating Elements */}
                <div className="absolute -top-8 -left-8 w-16 h-16 bg-green-400 dark:bg-green-600 rounded-2xl opacity-20 animate-float"></div>
                <div className="absolute -bottom-8 -right-8 w-24 h-24 bg-emerald-400 dark:bg-emerald-600 rounded-full opacity-20 animate-float animation-delay-2000"></div>
                
                {/* Phone Mockup */}
                <div className="relative z-10 transform hover:scale-105 transition-all duration-500 hover:rotate-1">
                  <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-[2.5rem] p-2.5 shadow-2xl">
                    <div className="bg-white dark:bg-gray-900 rounded-[2rem] overflow-hidden">
                      {/* Phone Screen */}
                      <div className="relative aspect-[9/19]">
                        {/* Status Bar */}
                        <div className="absolute top-0 left-0 right-0 h-7 bg-gradient-to-r from-green-500 to-emerald-600 flex items-center justify-between px-4 text-white text-xs">
                          <span>9:41</span>
                          <div className="flex gap-1">
                            <div className="w-3 h-3 rounded-full bg-white/30"></div>
                            <div className="w-3 h-3 rounded-full bg-white/30"></div>
                            <div className="w-3 h-3 rounded-full bg-white/30"></div>
                          </div>
                        </div>
                        
                        {/* App Content */}
                        <div className="pt-7 p-4 bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-gray-800 h-full">
                          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">My Farm Dashboard</h3>
                          
                          {/* Stats Cards */}
                          <div className="space-y-3">
                            <div className="bg-white dark:bg-gray-800 rounded-xl p-3 shadow-lg animate-pulse-slow">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">Crop Health</p>
                                  <p className="text-lg font-bold text-green-600">Excellent</p>
                                </div>
                                <Leaf className="h-8 w-8 text-green-500" />
                              </div>
                            </div>
                            
                            <div className="bg-white dark:bg-gray-800 rounded-xl p-3 shadow-lg animate-pulse-slow animation-delay-1000">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">Soil Moisture</p>
                                  <p className="text-lg font-bold text-blue-600">78%</p>
                                </div>
                                <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                  <div className="h-5 w-5 rounded-full bg-blue-500"></div>
                                </div>
                              </div>
                            </div>
                            
                            <div className="bg-white dark:bg-gray-800 rounded-xl p-3 shadow-lg animate-pulse-slow animation-delay-2000">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">Weather</p>
                                  <p className="text-lg font-bold text-orange-600">28°C</p>
                                </div>
                                <div className="text-3xl">☀️</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-white dark:bg-gray-900 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5 dark:opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }}></div>
        </div>

        <div className="container mx-auto max-w-7xl relative z-10">
          <div className="text-center mb-20 animate-fade-in-up">
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Powerful Features
              </span>
            </h2>
            <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Everything you need to manage your farm efficiently and boost productivity
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className="group animate-fade-in-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <Card className="p-8 border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-3 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 h-full relative overflow-hidden">
                    {/* Animated Background Gradient */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}></div>
                    
                    <div className="relative z-10">
                      <div className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 group-hover:rotate-6 transition-all duration-500`}>
                        <Icon className="h-8 w-8 text-white" />
                      </div>
                      <h3 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors duration-300">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </Card>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500 via-emerald-600 to-teal-600"></div>
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 animate-pulse-slow" style={{
            backgroundImage: 'radial-gradient(circle at 50% 50%, white 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }}></div>
        </div>

        <div className="container mx-auto max-w-5xl relative z-10">
          <div className="text-center space-y-8 animate-fade-in-up">
            <h2 className="text-5xl md:text-6xl font-bold text-white leading-tight">
              Ready to Transform Your Farm?
            </h2>
            <p className="text-xl md:text-2xl text-green-50 max-w-3xl mx-auto">
              Join thousands of farmers who are already using Smart Farmer to increase their yields and profits.
            </p>
            <div className="flex flex-col sm:flex-row gap-6 justify-center pt-6">
              <Button 
                size="lg"
                className="bg-white text-green-600 hover:bg-green-50 px-12 py-8 text-xl rounded-2xl shadow-2xl hover:shadow-white/50 transition-all duration-500 hover:-translate-y-2 hover:scale-105 group"
              >
                <Download className="h-7 w-7 mr-3 group-hover:animate-bounce" />
                Download for Android
              </Button>
            </div>
            
            {/* App Badges */}
            <div className="flex justify-center gap-4 pt-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 text-white font-semibold">
                ⭐ 4.8 Rating
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 text-white font-semibold">
                📱 10K+ Downloads
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 text-white font-semibold">
                🏆 #1 Farm App
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 bg-gray-950 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }}></div>
        </div>

        <div className="container mx-auto max-w-7xl relative z-10">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-6 group cursor-pointer">
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <Sprout className="h-7 w-7 text-white" />
                </div>
                <span className="text-3xl font-bold">Smart Farmer</span>
              </div>
              <p className="text-gray-400 text-lg max-w-md leading-relaxed">
                Empowering farmers with cutting-edge technology to build a sustainable and profitable future.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-lg mb-6">Product</h4>
              <ul className="space-y-3 text-gray-400">
                <li><a href="#" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">Features</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">Pricing</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">Download</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-lg mb-6">Company</h4>
              <ul className="space-y-3 text-gray-400">
                <li><a href="#" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">About</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">Contact</a></li>
                <li><Link href="/admin" className="hover:text-green-400 transition-colors duration-300 hover:translate-x-1 inline-block">Admin</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center">
            <p className="text-gray-400">&copy; 2024 Smart Farmer. All rights reserved. Made with 💚 for farmers.</p>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fade-in-right {
          from {
            opacity: 0;
            transform: translateX(30px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.8s ease-out forwards;
        }
        .animate-fade-in-right {
          animation: fade-in-right 0.8s ease-out forwards;
        }
        .animate-fade-in {
          animation: fade-in 1s ease-out forwards;
        }
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
        .animate-pulse-slow {
          animation: pulse-slow 2s ease-in-out infinite;
        }
        .animation-delay-200 {
          animation-delay: 200ms;
        }
        .animation-delay-400 {
          animation-delay: 400ms;
        }
        .animation-delay-600 {
          animation-delay: 600ms;
        }
        .animation-delay-800 {
          animation-delay: 800ms;
        }
        .animation-delay-1000 {
          animation-delay: 1000ms;
        }
        .animation-delay-2000 {
          animation-delay: 2000ms;
        }
        .animation-delay-4000 {
          animation-delay: 4000ms;
        }
      `}</style>
    </div>
  )
}
