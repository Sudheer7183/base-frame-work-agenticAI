// frontend/react-admin/src/pages/WCAudit/carrier-portal/CarrierPortalContext.tsx
//
// Provides live API data to every page in the carrier portal.
// CarrierPortalApp wraps all routes with this provider so each page
// can call useCarrierPortalData() without re-fetching.

import { createContext, useContext } from 'react'
import type { CarrierPortalData } from './types'

export const CarrierPortalContext = createContext<CarrierPortalData | null>(null)

export function useCarrierPortalData(): CarrierPortalData {
  const ctx = useContext(CarrierPortalContext)
  if (!ctx) throw new Error('useCarrierPortalData must be used inside CarrierPortalApp')
  return ctx
}
