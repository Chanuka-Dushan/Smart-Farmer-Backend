'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function DebugPage() {
  const [debugInfo, setDebugInfo] = useState<any>({
    clientSide: false,
    localStorage: false,
    envVar: 'Not loaded',
    apiTest: 'Not tested',
    error: null
  })

  useEffect(() => {
    const runDebug = async () => {
      try {
        const info: any = {
          clientSide: typeof window !== 'undefined',
          localStorage: typeof window !== 'undefined' && typeof localStorage !== 'undefined',
          envVar: process.env.NEXT_PUBLIC_API_URL || 'Not set',
          apiTest: 'Testing...',
          error: null
        }

        // Test API call
        try {
          const response = await fetch('/api/admin/users/stats', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            }
          })
          
          if (response.ok) {
            info.apiTest = `API working (${response.status})`
          } else {
            info.apiTest = `API error (${response.status}): ${await response.text()}`
          }
        } catch (apiError) {
          info.apiTest = `API failed: ${apiError instanceof Error ? apiError.message : 'Unknown error'}`
        }

        setDebugInfo(info)
      } catch (error) {
        setDebugInfo(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Unknown error'
        }))
      }
    }

    runDebug()
  }, [])

  return (
    <div className="container mx-auto p-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Dashboard Debug Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <strong>Client Side:</strong> 
            <span className={`ml-2 ${debugInfo.clientSide ? 'text-green-600' : 'text-red-600'}`}>
              {debugInfo.clientSide ? '✓ Yes' : '✗ No'}
            </span>
          </div>
          
          <div>
            <strong>LocalStorage Available:</strong> 
            <span className={`ml-2 ${debugInfo.localStorage ? 'text-green-600' : 'text-red-600'}`}>
              {debugInfo.localStorage ? '✓ Yes' : '✗ No'}
            </span>
          </div>
          
          <div>
            <strong>API URL:</strong> 
            <span className="ml-2 font-mono text-sm">{debugInfo.envVar}</span>
          </div>
          
          <div>
            <strong>API Test:</strong> 
            <span className="ml-2">{debugInfo.apiTest}</span>
          </div>
          
          {debugInfo.error && (
            <div>
              <strong>Error:</strong> 
              <span className="ml-2 text-red-600">{debugInfo.error}</span>
            </div>
          )}
          
          <div className="pt-4">
            <h3 className="font-semibold mb-2">Current URL Info:</h3>
            <div className="bg-gray-100 p-3 rounded text-sm font-mono">
              Location: {typeof window !== 'undefined' ? window.location.href : 'Server side'}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}