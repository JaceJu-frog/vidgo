// utils/peaks.ts
import { isProxy, toRaw, markRaw } from 'vue'

export function normalizePeaks(input: any): number[] {
  // 1) 去掉 Vue 的 Proxy
  const p: any = isProxy(input) ? toRaw(input) : input

  // 2) 已是普通数组
  if (Array.isArray(p)) return p.map(Number)

  // 3) TypedArray（Float32Array/Int16Array/...）
  if (p && typeof p === 'object' && typeof p.length === 'number' && ArrayBuffer.isView(p)) {
    // p.buffer 存在且不是 DataView → 视为 TypedArray
    return Array.from(p as unknown as Iterable<number>, Number)
  }

  // 4) 形如 {0: v0, 1: v1, ...} 的对象（常见于 JSON 化的 TypedArray）
  if (p && typeof p === 'object') {
    // 用数字键排序，确保顺序正确
    const keys = Object.keys(p)
      .map(Number)
      .sort((a, b) => a - b)
    return keys.map((k) => Number((p as Record<number, unknown>)[k]))
  }

  throw new Error('Unsupported peaks format')
}
