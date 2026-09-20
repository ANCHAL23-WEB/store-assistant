// ROUTE: /search
"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { searchProducts } from "@/lib/api";
import { useSearchParams } from "next/navigation";

function SearchPageInner() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const initialInputType = (searchParams.get("input_type") as "browse" | "voice" | "camera") ?? "browse";
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuery.trim()) {
      void performSearch(initialQuery, initialInputType);
    }
  }, []);

  async function performSearch(q: string, inputType: "browse" | "voice" | "camera" = "browse") {
    setLoading(true);
    try {
      const data = await searchProducts(q, 10, inputType);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    void performSearch(query);
  }

  return (
    <main style={{ padding: 24, maxWidth: 600, margin: "0 auto" }}>
      <h1>Search Products</h1>
      <form onSubmit={handleSearch} style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a product name..."
          style={{ flex: 1, padding: 10, fontSize: 16 }}
        />
        <button type="submit" style={{ padding: "10px 20px" }}>Search</button>
      </form>
{loading && <p>Searching...</p>}

      {!loading && results.length === 0 && query.trim() && (
        <p style={{ color: "#666" }}>No matching products found. This item may not be available in our store.</p>
      )}

      <ul style={{ listStyle: "none", padding: 0 }}>
      
        {results.map((p) => (
          <li key={p.product_id} style={{ marginBottom: 12 }}>
            <Link href={`/product/${p.product_id}`}>{p.name}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p style={{ padding: 24 }}>Loading...</p>}>
      <SearchPageInner />
    </Suspense>
  );
}