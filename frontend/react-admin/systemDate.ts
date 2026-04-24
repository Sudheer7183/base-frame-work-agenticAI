let runtimeOverride: Date | null = null

function parseEnvDate(): Date | null {
  const envDate = import.meta.env.VITE_SYSTEM_DATE

  console.log("env date",envDate);
  
  if (!envDate) return null

  const parsed = new Date(envDate)
  return isNaN(parsed.getTime()) ? null : parsed
}

export function setSystemDate(date: Date | null) {
  runtimeOverride = date
}

export function getSystemDate(): Date {
  if (runtimeOverride) return runtimeOverride

  const envDate = parseEnvDate()
  if (envDate) return envDate

  return new Date()
}