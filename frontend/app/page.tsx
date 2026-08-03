"use client";

import { FormEvent, useState } from "react";

import { Product, searchProducts } from "@/lib/api";

const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function visibleSpecs(specs: Product["specs"]) {
  return Object.entries(specs).slice(0, 3);
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setIsLoading(true);
    setError("");
    setHasSearched(true);
    try {
      setProducts(await searchProducts(trimmedQuery, 10));
    } catch {
      setProducts([]);
      setError("Backend not reachable. Please make sure the API is running.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12 text-slate-900 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <p className="mb-2 text-sm font-semibold tracking-wide text-blue-700 uppercase">
            Retail Store Assistant
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Find the right product
          </h1>
          <p className="mt-2 text-slate-600">
            Search by product name, brand, or the features you need.
          </p>
        </header>

        <form onSubmit={handleSearch} className="mb-8 flex max-w-2xl gap-3">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. 55 inch Samsung 4K TV"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 outline-none ring-blue-500 transition focus:ring-2"
            aria-label="Search products"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {error && (
          <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </p>
        )}

        {isLoading && <p className="text-slate-600">Searching products...</p>}

        {!isLoading && hasSearched && !error && products.length === 0 && (
          <p className="rounded-lg border border-slate-200 bg-white p-6 text-slate-600">
            No products found
          </p>
        )}

        {!isLoading && products.length > 0 && (
          <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <article
                key={product.product_id}
                className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
              >
                <div className="flex aspect-[4/3] items-center justify-center bg-slate-100 text-sm font-medium text-slate-400">
                  Product image
                </div>
                <div className="p-4">
                  <p className="text-sm font-medium text-blue-700">{product.brand}</p>
                  <h2 className="mt-1 min-h-12 font-semibold leading-6">{product.name}</h2>
                  <p className="mt-3 text-lg font-bold">{rupees.format(product.price)}</p>
                  <dl className="mt-4 space-y-1 text-sm text-slate-600">
                    {visibleSpecs(product.specs).map(([key, value]) => (
                      <div key={key} className="flex gap-1">
                        <dt className="capitalize">{key.replaceAll("_", " ")}:</dt>
                        <dd className="truncate font-medium text-slate-700">
                          {typeof value === "object" ? JSON.stringify(value) : String(value)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </article>
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
