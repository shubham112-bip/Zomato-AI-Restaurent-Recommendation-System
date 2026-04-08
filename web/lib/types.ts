export type RecommendationMeta = {
  candidates_considered: number;
  constraints_relaxed: boolean;
  model: string;
  prompt_version: string;
  cuisine_resolved?: string | null;
};

export type RestaurantRecommendation = {
  name: string;
  cuisine: string;
  rating: number | null;
  estimated_cost: string;
  explanation: string;
  rank: number;
};

export type RecommendationResponse = {
  summary: string | null;
  recommendations: RestaurantRecommendation[];
  meta: RecommendationMeta;
  degraded: boolean;
  message?: string | null;
};
