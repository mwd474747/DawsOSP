import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Basic health check
    return NextResponse.json({
      status: 'healthy',
      service: 'DawsOS UI',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    })
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        service: 'DawsOS UI',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}
