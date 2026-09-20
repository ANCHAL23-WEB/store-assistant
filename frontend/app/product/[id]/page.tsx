"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import Image from "next/image";

import {
  ProductDetail,
  checkPriceMatch,
  fetchProductById,
  PriceMatchResponse,
} from "@/lib/api";

const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [competitorPrice, setCompetitorPrice] = useState("");
  const [source, setSource] = useState("");
  const [selectedStoreId, setSelectedStoreId] = useState<number | null>(null);
  const [priceMatchResult, setPriceMatchResult] = useState<PriceMatchResponse | null>(null);
  const [isCheckingMatch, setIsCheckingMatch] = useState(false);
  const [priceMatchError, setPriceMatchError] = useState("");

   useEffect(() => {
    if (!Number.isFinite(productId)) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- kicks off loading state for a data fetch triggered by productId change, not a render-loop issue
    setIsLoading(true);
    setError("");
    fetchProductById(productId)
      .then((result) => {
        setProduct(result);
        setSelectedStoreId(result.inventory[0]?.store_id ?? null);
      })
      .catch(() => setError("Could not load this product. Please make sure the backend is running."))
      .finally(() => setIsLoading(false));
  }, [productId]);

  async function handlePriceMatchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!product || selectedStoreId === null) return;

    const parsedPrice = Number(competitorPrice);
    if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
      setPriceMatchError("Enter a valid competitor price.");
      return;
    }

    setIsCheckingMatch(true);
    setPriceMatchError("");
    setPriceMatchResult(null);
    try {
      const result = await checkPriceMatch({
        productId: product.product_id,
        storeId: selectedStoreId,
        competitorPrice: parsedPrice,
        source: source.trim() || "Unknown source",
      });
      setPriceMatchResult(result);
    } catch {
      setPriceMatchError("Could not check the price match right now. Please try again.");
    } finally {
      setIsCheckingMatch(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="mb-6 inline-flex items-center gap-1 text-sm font-semibold text-blue-700 hover:underline">
          ← Back to home
        </Link>

        {isLoading && <p className="text-lg text-slate-600">Loading product…</p>}
        {error && (
          <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </p>
        )}

        {product && (
          <>
                        {product.image_url && (
              <div className="relative mb-6 h-64 w-full overflow-hidden rounded-2xl border border-slate-200 sm:h-80">
                <Image
                  src={product.image_url}
                  alt={product.name}
                  fill
                  className="object-cover"
                  unoptimized
                />
              </div>
            )}

            <p className="mb-1 text-sm font-semibold uppercase tracking-wide text-blue-700">
              {product.brand} · {product.category}
            </p>
            <h1 className="mb-3 text-3xl font-bold tracking-tight sm:text-4xl">{product.name}</h1>
            <p className="mb-8 text-4xl font-extrabold text-blue-700">{rupees.format(product.price)}</p>

            {/* Specifications */}
            <section className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="mb-4 text-xl font-bold">Features</h2>
              <dl className="grid gap-3 sm:grid-cols-2">
                {Object.entries(product.specs).map(([key, value]) => (
                  <div key={key} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
                    <dt className="capitalize text-slate-500">{key.replaceAll("_", " ")}</dt>
                    <dd className="font-semibold text-slate-800">
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </dd>
                  </div>
                ))}
                {product.colors.length > 0 && (
                  <div className="flex justify-between border-b border-slate-100 pb-2 text-sm">
                    <dt className="text-slate-500">Colors</dt>
                    <dd className="font-semibold text-slate-800">{product.colors.join(", ")}</dd>
                  </div>
                )}
              </dl>
            </section>

            {/* Availability */}
            <section className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="mb-4 text-xl font-bold">Availability &amp; Delivery</h2>
              {product.inventory.length === 0 ? (
                <p className="text-slate-600">No stock information available.</p>
              ) : (
                <ul className="space-y-3">
                  {product.inventory.map((record) => (
                    <li
                      key={record.store_id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50 p-4"
                    >
                      <div>
                        <p className="font-semibold">{record.store_name}</p>
                        <p className="text-sm text-slate-500">{record.location}, {record.city}</p>
                      </div>
                      <div className="text-right">
                        {record.stock_qty > 0 ? (
                          <p className="font-semibold text-emerald-700">{record.stock_qty} in stock</p>
                        ) : (
                          <p className="font-semibold text-red-600">
                            Out of stock
                            {record.restock_eta_days != null && ` — restocks in ${record.restock_eta_days} days`}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Price Match */}
            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="mb-1 text-xl font-bold">Found it cheaper elsewhere?</h2>
              <p className="mb-4 text-sm text-slate-600">
                Enter a competitor&apos;s price and we&apos;ll tell you the best price we can offer.
              </p>

              <form onSubmit={handlePriceMatchSubmit} className="space-y-4">
                {product.inventory.length > 1 && (
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="store-select">
                      Store
                    </label>
                    <select
                      id="store-select"
                      value={selectedStoreId ?? ""}
                      onChange={(event) => setSelectedStoreId(Number(event.target.value))}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    >
                      {product.inventory.map((record) => (
                        <option key={record.store_id} value={record.store_id}>
                          {record.store_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="competitor-price">
                      Competitor price (₹)
                    </label>
                    <input
                      id="competitor-price"
                      type="number"
                      min="1"
                      step="1"
                      value={competitorPrice}
                      onChange={(event) => setCompetitorPrice(event.target.value)}
                      placeholder="e.g. 40000"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="source">
                      Where did you see it?
                    </label>
                    <input
                      id="source"
                      type="text"
                      value={source}
                      onChange={(event) => setSource(event.target.value)}
                      placeholder="e.g. Amazon, Reliance Digital"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isCheckingMatch || selectedStoreId === null}
                  className="w-full rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
                >
                  {isCheckingMatch ? "Checking…" : "Check Best Price"}
                </button>
              </form>

              {priceMatchError && <p role="alert" className="mt-4 text-sm text-red-700">{priceMatchError}</p>}

              {priceMatchResult && (
                <div
                  className={`mt-5 rounded-xl border p-5 ${
                    priceMatchResult.approved
                      ? "border-emerald-200 bg-emerald-50"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <p className="text-2xl font-bold">
                    {priceMatchResult.approved
                      ? `We can offer ${rupees.format(priceMatchResult.final_price)}`
                      : `Our price already stands at ${rupees.format(priceMatchResult.store_price)}`}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">{priceMatchResult.reason}</p>
                  {priceMatchResult.approved && priceMatchResult.discount_applied > 0 && (
                    <p className="mt-2 text-sm font-medium text-emerald-700">
                      You save {rupees.format(priceMatchResult.discount_applied)}
                    </p>
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}