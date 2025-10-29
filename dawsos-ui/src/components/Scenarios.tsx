'use client'

import { ModernScenarios } from './ModernScenarios'

interface ScenariosProps {
  portfolioId?: string;
}

export function Scenarios({ portfolioId = 'main-portfolio' }: ScenariosProps) {
  // Use the modern scenarios component with all the glassmorphic design and animations
  return <ModernScenarios portfolioId={portfolioId} />
}
