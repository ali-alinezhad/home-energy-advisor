import axios from "axios"

export interface Recommendation {
  title: string
  description: string
  priority: "high" | "medium" | "low"
}

export interface AdviceResponse {
  recommendations: Recommendation[]
}

export interface HomePayload {
  size: number
  year_built: number
  heating_type: "gas" | "oil" | "electric" | "heat_pump"
  insulation_level: "low" | "medium" | "high"
}

export interface HomeResponse extends HomePayload {
  id: number
  latest_advice: AdviceResponse | null
  advice_generated_at: string | null
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json"
  }
})

export async function createHome(payload: HomePayload): Promise<HomeResponse> {
  const response = await api.post("/homes", payload)
  return response.data
}

export async function getHome(homeId: number): Promise<HomeResponse> {
  const response = await api.get(`/homes/${homeId}`)
  return response.data
}

export async function getAdvice(homeId: number): Promise<AdviceResponse> {
  const response = await api.post(`/homes/${homeId}/advice`)
  return response.data
}
