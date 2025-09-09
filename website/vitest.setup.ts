import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock createObjectURL for tests involving file downloads
// @ts-ignore
if (!global.URL.createObjectURL) {
  // @ts-ignore
  global.URL.createObjectURL = vi.fn()
}
// @ts-ignore
if (!global.URL.revokeObjectURL) {
  // @ts-ignore
  global.URL.revokeObjectURL = vi.fn()
}
