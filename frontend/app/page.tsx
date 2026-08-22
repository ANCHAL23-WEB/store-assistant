// ROUTE: / (home)
"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-10 bg-slate-950 px-4 py-8 text-white">
      <h1 className="text-4xl font-bold">Store Assistant</h1>

      <div className="flex w-full max-w-md flex-col gap-6">
        <Link
          href="/scan"
          className="flex items-center justify-center gap-4 rounded-2xl bg-blue-600 py-8 text-3xl font-semibold hover:bg-blue-700"
        >
          📷 Scan
        </Link>
        <Link
          href="/speak"
          className="flex items-center justify-center gap-4 rounded-2xl bg-green-600 py-8 text-3xl font-semibold hover:bg-green-700"
        >
          🎤 Speak
        </Link>
        <Link
          href="/search"
          className="flex items-center justify-center gap-4 rounded-2xl bg-purple-600 py-8 text-3xl font-semibold hover:bg-purple-700"
        >
          ⌨️ Type
        </Link>
      </div>
    </main>
  );
}