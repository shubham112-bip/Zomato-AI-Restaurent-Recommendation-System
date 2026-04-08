"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { RestaurantRecommendation } from "@/lib/types";

const FOOD_IMAGES = [
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=400&fit=crop",
  "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=400&fit=crop",
  "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=400&fit=crop",
  "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=400&fit=crop",
];

type Props = {
  item: RestaurantRecommendation;
  imageIndex: number;
};

export function RecommendationCard({ item, imageIndex }: Props) {
  const photoUrl = FOOD_IMAGES[imageIndex % FOOD_IMAGES.length];
  const [photoOk, setPhotoOk] = useState(true);

  useEffect(() => {
    setPhotoOk(true);
  }, [photoUrl, imageIndex]);

  const rating =
    item.rating != null && !Number.isNaN(Number(item.rating))
      ? Number(item.rating).toFixed(1)
      : "—";

  return (
    <article className="flex gap-4 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="relative h-28 w-28 shrink-0 overflow-hidden rounded-lg bg-zinc-200 sm:h-32 sm:w-32">
        {/* Always-visible base so the slot never looks like a missing asset */}
        <div
          className="absolute inset-0 z-0 bg-gradient-to-br from-amber-200 via-orange-300 to-[#E23744]/60"
          aria-hidden
        />
        {photoOk ? (
          <Image
            src={photoUrl}
            alt=""
            fill
            className="z-[1] object-cover"
            sizes="(max-width: 768px) 112px, 128px"
            onError={() => setPhotoOk(false)}
          />
        ) : (
          <div
            className="absolute inset-0 z-[1] flex items-center justify-center bg-gradient-to-t from-orange-400/90 to-amber-200 text-4xl"
            aria-hidden
          >
            🍽️
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="truncate text-lg font-bold text-[#1C1C1C]">{item.name}</h3>
          <span className="flex shrink-0 items-center gap-0.5 text-amber-500">
            <span aria-hidden>★</span>
            <span className="text-sm font-semibold text-[#1C1C1C]">{rating}</span>
          </span>
        </div>
        <p className="mt-1 text-sm text-[#696969]">
          {item.cuisine} · {item.estimated_cost}
        </p>
        <div className="mt-3 rounded-lg bg-zinc-100 px-3 py-2 text-sm text-[#1C1C1C]">
          <span className="font-semibold text-[#E23744]">AI Reason: </span>
          {item.explanation}
        </div>
      </div>
    </article>
  );
}
