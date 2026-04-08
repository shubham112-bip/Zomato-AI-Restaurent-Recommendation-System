import type { RecommendationResponse } from "./types";

export async function fetchHealth(): Promise<{ status: string; dataset_ready?: boolean }> {
  const r = await fetch("/health", { cache: "no-store" });
  if (!r.ok) throw new Error("Health check failed");
  return r.json();
}

export async function fetchLocations(): Promise<string[]> {
  const r = await fetch("/api/v1/locations", { cache: "no-store" });
  if (!r.ok) throw new Error("Failed to load locations");
  const data = await r.json();
  return Array.isArray(data.locations) ? data.locations : [];
}

export async function fetchCuisines(): Promise<string[]> {
  const r = await fetch("/api/v1/cuisines", { cache: "no-store" });
  if (!r.ok) throw new Error("Failed to load cuisines");
  const data = await r.json();
  return Array.isArray(data.cuisines) ? data.cuisines : [];
}

export async function postRecommendations(body: Record<string, unknown>): Promise<RecommendationResponse> {
  const r = await fetch("/api/v1/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detail = data.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ")
          : r.statusText;
    throw new Error(msg || `Request failed (${r.status})`);
  }
  return data as RecommendationResponse;
}
