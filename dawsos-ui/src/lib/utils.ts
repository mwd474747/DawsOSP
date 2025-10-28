/**
 * Utility functions for DawsOS UI
 * 
 * Purpose: Common utility functions and helpers
 * Updated: 2025-10-28
 * Priority: P0 (Critical for UI components)
 */

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}