'use client'

import { useEffect, useState } from 'react'
import { Card } from "@/components/ui/card"

interface HealthCheck {
  client: boolean
  localStorage: boolean
  apiUrl: string
  backendHealth: string
  timestamp: string
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthCheck | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const healthData: HealthCheck = {
          client: true,
          localStorage: typeof window !== 'undefined' && typeof localStorage !== 'undefined',
          apiUrl: process.env.NEXT_PUBLIC_API_URL || 'Not set',
          backendHealth: 'Checking...',
          timestamp: new Date().toISOString()
        }

        // Test API connection
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'test@test.com', password: 'test' })
          })
          healthData.backendHealth = `API reachable (${response.status})`
        } catch (apiError) {
          healthData.backendHealth = `API error: ${apiError instanceof Error ? apiError.message : 'Unknown error'}`
        }

        setHealth(healthData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    }

    checkHealth()
  }, [])

  if (error) {
    return (
      <div className="container mx-auto p-8">
        <Card className="p-6">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Health Check Error</h1>
          <p className="text-red-500">{error}</p>
        </Card>
      </div>
    )
  }

  if (!health) {
    return (
      <div className="container mx-auto p-8">
        <Card className="p-6">
          <h1 className="text-2xl font-bold mb-4">Health Check</h1>
          <p>Loading...</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      <Card className="p-6">
        <h1 className="text-2xl font-bold mb-4">Health Check</h1>
        <div className="space-y-2">
          <div>
            <strong>Client Side:</strong> 
            <span className={health.client ? 'text-green-600 ml-2' : 'text-red-600 ml-2'}>
              {health.client ? '✓ Working' : '✗ Failed'}
            </span>
          </div>
          
          <div>
            <strong>LocalStorage:</strong> 
            <span className={health.localStorage ? 'text-green-600 ml-2' : 'text-red-600 ml-2'}>
              {health.localStorage ? '✓ Available' : '✗ Not Available'}
            </span>
          </div>
          
          <div>
            <strong>API URL:</strong> 
            <span className="ml-2 font-mono">{health.apiUrl}</span>
          </div>
          
          <div>
            <strong>Backend Health:</strong> 
            <span className="ml-2">{health.backendHealth}</span>
          </div>
          
          <div>
            <strong>Timestamp:</strong> 
            <span className="ml-2 text-sm text-gray-600">{health.timestamp}</span>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-100 rounded">
          <h2 className="font-semibold mb-2">Debug Information:</h2>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      </Card>
    </div>
  )
}