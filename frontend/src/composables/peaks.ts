// Utility functions for processing audio waveform peak data
import { isProxy, toRaw, markRaw } from 'vue'

export function normalizePeaks(input: any): number[] {
  // Remove Vue proxy wrapper if present
  const p: any = isProxy(input) ? toRaw(input) : input

  // Handle standard array format
  if (Array.isArray(p)) return p.map(Number)

  // Handle TypedArray formats (Float32Array/Int16Array/etc.)
  if (p && typeof p === 'object' && typeof p.length === 'number' && ArrayBuffer.isView(p)) {
    // Convert TypedArray to regular number array
    return Array.from(p as unknown as Iterable<number>, Number)
  }

  // Handle object with numeric keys (common when TypedArray is JSON serialized)
  if (p && typeof p === 'object') {
    // Sort by numeric keys to maintain proper order
    const keys = Object.keys(p)
      .map(Number)
      .sort((a, b) => a - b)
    return keys.map((k) => Number((p as Record<number, unknown>)[k]))
  }

  throw new Error('Unsupported peaks format')
}
