"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { fetchCuisines, fetchHealth, fetchLocations, postRecommendations } from "@/lib/api";
import type { RecommendationResponse, RestaurantRecommendation } from "@/lib/types";
import { RecommendationCard } from "./RecommendationCard";

const QUICK_TAGS = ["Indian", "South Indian", "Chinese", "Italian"];

export function RecommendationApp() {
  const [datasetReady, setDatasetReady] = useState(true);
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisineList, setCuisineList] = useState<string[]>([]);

  const [location, setLocation] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [minRating, setMinRating] = useState("");
  const [cravings, setCravings] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [showCuisineSuggestions, setShowCuisineSuggestions] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const h = await fetchHealth();
        if (cancelled) return;
        if (h.dataset_ready === false) {
          setDatasetReady(false);
          return;
        }
        setDatasetReady(true);
        const [locs, cuis] = await Promise.all([fetchLocations(), fetchCuisines()]);
        if (cancelled) return;
        setLocations(locs);
        setCuisineList(cuis);
        setLocation((prev) => {
          if (prev) return prev;
          if (!locs.length) return "";
          return locs.find((x) => x.toLowerCase() === "bangalore") ?? locs[0];
        });
      } catch {
        if (!cancelled) setDatasetReady(true);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (datasetReady) return;
    const id = setInterval(async () => {
      try {
        const h = await fetchHealth();
        if (h.dataset_ready !== false) {
          setDatasetReady(true);
          const [locs, cuis] = await Promise.all([fetchLocations(), fetchCuisines()]);
          setLocations(locs);
          setCuisineList(cuis);
          setLocation((prev) => {
            if (prev) return prev;
            if (!locs.length) return "";
            return locs.find((x) => x.toLowerCase() === "bangalore") ?? locs[0];
          });
        }
      } catch {
        /* ignore */
      }
    }, 3000);
    return () => clearInterval(id);
  }, [datasetReady]);

  const applyTag = (tag: string) => {
    setCuisine(tag);
  };

  const filteredCuisines = cuisineList
    .filter((c) => c.toLowerCase().includes(cuisine.trim().toLowerCase()))
    .slice(0, 8);
  const filteredLocations = locations
    .filter((loc) => loc.toLowerCase().includes(location.trim().toLowerCase()))
    .slice(0, 8);

  const buildExtras = () => {
    if (!cravings.trim()) return undefined;
    return cravings.trim();
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setResult(null);

    if (!location.trim()) {
      setError("Please choose a location.");
      return;
    }

    const payload: Record<string, unknown> = { location: location.trim() };
    const b = budgetMax.trim();
    if (b) {
      const n = parseFloat(b);
      if (!Number.isFinite(n) || n <= 0) {
        setError("Enter a valid max budget (INR) or leave blank.");
        return;
      }
      payload.budget_max_inr = n;
    }
    if (cuisine.trim()) payload.cuisine = cuisine.trim();
    const mr = minRating.trim();
    if (mr) {
      const x = parseFloat(mr);
      if (!Number.isFinite(x) || x < 0 || x > 5) {
        setError("Minimum rating must be 0–5 or blank.");
        return;
      }
      payload.min_rating = x;
    }
    const ex = buildExtras();
    if (ex) payload.extras = ex;

    setLoading(true);
    try {
      const data = await postRecommendations(payload);
      setResult(data);
      let msg: string | null = null;
      if (data.meta?.cuisine_resolved) {
        msg = `Closest cuisine match: "${data.meta.cuisine_resolved}".`;
      }
      if (data.message) msg = msg ? `${msg} ${data.message}` : data.message;
      setInfo(msg);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const recs: RestaurantRecommendation[] = result?.recommendations ?? [];

  return (
    <>
      <section className="relative min-h-[520px] overflow-hidden">
        <div className="absolute inset-0">
          <Image
            src="/hero-bg.png"
            alt=""
            fill
            className="object-cover brightness-[0.45]"
            priority
            sizes="100vw"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/50 to-black/70" />
        </div>

        <div className="relative z-10 mx-auto max-w-3xl px-4 py-12 sm:px-6 sm:py-16">
          {!datasetReady && (
            <p className="mb-4 rounded-lg bg-white/90 px-4 py-3 text-center text-sm text-[#1C1C1C] shadow">
              Loading restaurant dataset… You can stay on this page until ready.
            </p>
          )}

          <form onSubmit={onSubmit} className="rounded-2xl bg-white p-6 shadow-xl sm:p-8">
            <h2 className="text-center text-xl font-bold text-[#1C1C1C] sm:text-2xl">
              Find Your Perfect Meal with Zomato AI
            </h2>

            <div className="mt-2">
              <span className="text-xs font-medium text-[#696969]">Cuisine</span>
              <div className="relative mt-1">
                <input
                  className="w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-sm text-[#1C1C1C] outline-none placeholder:text-zinc-400 focus:border-[#E23744]"
                  placeholder="Hi! Which Cuisine are you craving today?"
                  value={cuisine}
                  onChange={(e) => {
                    setCuisine(e.target.value);
                    setShowCuisineSuggestions(true);
                  }}
                  onFocus={() => setShowCuisineSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowCuisineSuggestions(false), 120)}
                  aria-label="Cuisine"
                />
                {showCuisineSuggestions && filteredCuisines.length > 0 && (
                  <div className="absolute z-20 mt-1 max-h-52 w-full overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
                    {filteredCuisines.map((c) => (
                      <button
                        key={c}
                        type="button"
                        className="block w-full px-3 py-2 text-left text-sm text-[#1C1C1C] hover:bg-zinc-100"
                        onMouseDown={() => {
                          setCuisine(c);
                          setShowCuisineSuggestions(false);
                        }}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {QUICK_TAGS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => applyTag(tag)}
                  className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-[#696969] hover:border-[#E23744] hover:text-[#E23744]"
                >
                  {tag}
                </button>
              ))}
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-medium text-[#696969]">
                  Location <span className="text-[#E23744]">*</span>
                </span>
                <div className="relative mt-1">
                  <input
                    required
                    className="w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-sm text-[#1C1C1C] outline-none placeholder:text-zinc-400 focus:border-[#E23744]"
                    placeholder="Type location (e.g. Koramangala)"
                    value={location}
                    onChange={(e) => {
                      setLocation(e.target.value);
                      setShowLocationSuggestions(true);
                    }}
                    onFocus={() => setShowLocationSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 120)}
                  />
                  {showLocationSuggestions && filteredLocations.length > 0 && (
                    <div className="absolute z-20 mt-1 max-h-52 w-full overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
                      {filteredLocations.map((loc) => (
                        <button
                          key={loc}
                          type="button"
                          className="block w-full px-3 py-2 text-left text-sm text-[#1C1C1C] hover:bg-zinc-100"
                          onMouseDown={() => {
                            setLocation(loc);
                            setShowLocationSuggestions(false);
                          }}
                        >
                          {loc}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[#696969]">Max budget (₹ for two)</span>
                <input
                  type="number"
                  min={1}
                  step={1}
                  className="no-spin mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-sm text-[#1C1C1C] outline-none focus:border-[#E23744]"
                  placeholder="e.g. 1500"
                  value={budgetMax}
                  onChange={(e) => setBudgetMax(e.target.value)}
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[#696969]">Minimum rating</span>
                <input
                  type="number"
                  min={0}
                  max={5}
                  step={0.1}
                  className="no-spin mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-sm text-[#1C1C1C] outline-none focus:border-[#E23744]"
                  placeholder="e.g. 4"
                  value={minRating}
                  onChange={(e) => setMinRating(e.target.value)}
                />
              </label>
            </div>

            <label className="mt-4 block">
              <span className="text-xs font-medium text-[#696969]">Specific cravings</span>
              <input
                className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-sm text-[#1C1C1C] outline-none focus:border-[#E23744]"
                placeholder="e.g. Biryani, Butter Chicken"
                value={cravings}
                onChange={(e) => setCravings(e.target.value)}
              />
            </label>

            {error && (
              <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {error}
              </p>
            )}
            {info && !error && (
              <p className="mt-4 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">{info}</p>
            )}

            <button
              type="submit"
              disabled={loading || !datasetReady}
              className="mt-6 w-full rounded-xl bg-[#E23744] py-3.5 text-center text-base font-semibold text-white shadow hover:bg-[#c42e3a] disabled:opacity-50"
            >
              {loading ? "Getting recommendations…" : "Get Recommendations"}
            </button>
          </form>
        </div>
      </section>

      {result && (
        <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <h2 className="mb-6 text-2xl font-bold text-[#1C1C1C]">Personalized Picks for You</h2>
          {result.summary && (
            <p className="mb-6 rounded-xl border border-zinc-200 bg-white p-4 text-[#696969] shadow-sm">
              {result.summary}
            </p>
          )}
          <div className="grid gap-6 md:grid-cols-2">
            {recs.map((item, i) => (
              <RecommendationCard key={`${item.name}-${item.rank}-${i}`} item={item} imageIndex={i} />
            ))}
          </div>
          {recs.length === 0 && (
            <p className="text-center text-[#696969]">No recommendations returned. Try adjusting filters.</p>
          )}
        </section>
      )}
    </>
  );
}
