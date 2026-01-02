import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8080'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    console.log('Login API - Backend URL:', BACKEND_URL)
    console.log('Login attempt for:', body.email)

    const response = await fetch(`${BACKEND_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      console.error('Login failed:', data)
      return NextResponse.json(data, { status: response.status })
    }

    console.log('Login successful')
    return NextResponse.json(data)
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { detail: `Internal server error: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
