"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";

import { Product, searchProducts, searchProductsByImage } from "@/lib/api";

const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

interface SpeechRecognitionEvent extends Event {
  results: {
    [index: number]: {
      [index: number]: { transcript: string };
    };
    length: number;
  };
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  start: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

function visibleSpecs(specs: Product["specs"]) {
  return Object.entries(specs).slice(0, 3);
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [isVoiceSupported, setIsVoiceSupported] = useState<boolean | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState("");
  const cameraInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsVoiceSupported(Boolean(window.SpeechRecognition || window.webkitSpeechRecognition));
  }, []);

  async function runSearch(searchQuery: string) {
    if (!searchQuery) return;

    setIsLoading(true);
    setError("");
    setScanMessage("");
    setHasSearched(true);
    try {
      setProducts(await searchProducts(searchQuery, 10));
    } catch {
      setProducts([]);
      setError("Backend not reachable. Please make sure the API is running.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    await runSearch(trimmedQuery);
  }

  function startVoiceSearch() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setIsVoiceSupported(false);
      return;
    }

    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event) => {
      setIsListening(false);
      setVoiceError(
        event.error === "not-allowed" || event.error === "service-not-allowed"
          ? "Microphone permission was denied. Allow microphone access and try again."
          : "Voice search could not understand that. Please try again.",
      );
    };
    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      setQuery(transcript);
      void runSearch(transcript);
    };

    setVoiceError("");
    setIsListening(true);
    try {
      recognition.start();
    } catch {
      setIsListening(false);
      setVoiceError("Voice search could not start. Please try again.");
    }
  }

  async function handleImageSelected(event: ChangeEvent<HTMLInputElement>) {
    const image = event.target.files?.[0];
    event.target.value = "";
    if (!image) return;

    setIsScanning(true);
    setError("");
    setScanMessage("");
    setHasSearched(true);
    try {
      const response = await searchProductsByImage(image);
      setProducts(response.products);
      setScanMessage(response.message ?? "");
    } catch {
      setProducts([]);
      setError("Could not scan that image. Please make sure the backend is running.");
    } finally {
      setIsScanning(false);
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

        <form onSubmit={handleSearch} className="mb-3 flex max-w-2xl gap-3">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. 55 inch Samsung 4K TV"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 outline-none ring-blue-500 transition focus:ring-2"
            aria-label="Search products"
          />
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleImageSelected}
            className="hidden"
            aria-label="Take or select a product image"
          />
          {isVoiceSupported && (
            <button
              type="button"
              onClick={startVoiceSearch}
              disabled={isLoading || isListening || isScanning}
              className="rounded-lg border border-blue-700 px-4 py-3 font-semibold text-blue-700 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
              aria-label="Search with voice"
              aria-pressed={isListening}
              title="Search with voice"
            >
              <span aria-hidden="true">🎤</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            disabled={isLoading || isListening || isScanning}
            className="rounded-lg border border-blue-700 px-4 py-3 font-semibold text-blue-700 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
            aria-label="Search with camera"
            title="Search with camera"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 fill-none stroke-current stroke-2">
              <path d="M4 7h3l1.5-2h7L17 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" />
              <circle cx="12" cy="13" r="3" />
            </svg>
          </button>
          <button
            type="submit"
            disabled={isLoading || isScanning || !query.trim()}
            className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {isListening && (
          <p className="mb-3 flex items-center gap-2 text-sm font-medium text-blue-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-blue-700" />
            Listening...
          </p>
        )}
        {isVoiceSupported === false && (
          <p className="mb-3 text-sm text-slate-500">Voice search not supported in this browser.</p>
        )}
        {voiceError && <p role="alert" className="mb-3 text-sm text-red-700">{voiceError}</p>}
        {isScanning && (
          <p className="mb-3 flex items-center gap-2 text-sm font-medium text-blue-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-blue-700" />
            Scanning...
          </p>
        )}
        {scanMessage && <p className="mb-3 text-sm text-slate-600">{scanMessage}</p>}

        {error && (
          <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </p>
        )}

        {isLoading && <p className="text-slate-600">Searching products...</p>}

        {!isLoading && !isScanning && hasSearched && !error && !scanMessage && products.length === 0 && (
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
