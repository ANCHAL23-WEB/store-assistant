"use client";

import { BrowserMultiFormatReader } from "@zxing/browser";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { fetchProductByBarcode } from "@/lib/api";

export default function ScanPage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const readerRef = useRef<BrowserMultiFormatReader | null>(null);
  const hasResolvedRef = useRef(false);

  const [status, setStatus] = useState<"starting" | "scanning" | "looking-up" | "error">(
    "starting",
  );
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const reader = new BrowserMultiFormatReader();
    readerRef.current = reader;
    let controls: { stop: () => void } | undefined;

    async function startScanning() {
      try {
        controls = await reader.decodeFromVideoDevice(
          undefined,
          videoRef.current ?? undefined,
          (result, decodeError) => {
            if (hasResolvedRef.current) return;
            if (result) {
              hasResolvedRef.current = true;
              controls?.stop();
              void handleBarcodeDetected(result.getText());
              return;
            }
            // decodeError fires continuously while no barcode is in view; that's expected and ignored.
            void decodeError;
          },
        );
        setStatus("scanning");
      } catch {
        setStatus("error");
        setErrorMessage(
          "Could not access the camera. Please allow camera permission and reload the page.",
        );
      }
    }

    async function handleBarcodeDetected(barcode: string) {
      setStatus("looking-up");
      try {
        const product = await fetchProductByBarcode(barcode);
        router.push(`/product/${product.product_id}`);
      } catch {
        setStatus("error");
        setErrorMessage(`No product found for barcode ${barcode}. Try again or type the name instead.`);
      }
    }

    void startScanning();

    return () => {
      controls?.stop();
    };
  }, [router]);

  function retry() {
    hasResolvedRef.current = false;
    setErrorMessage("");
    setStatus("starting");
    window.location.reload();
  }

  return (
    <main className="flex min-h-screen flex-col items-center bg-slate-950 px-4 py-8 text-white">
      <div className="mx-auto w-full max-w-xl">
        <Link href="/" className="mb-6 inline-flex items-center gap-1 text-sm font-semibold text-blue-300 hover:underline">
          ← Back to home
        </Link>

        <h1 className="mb-2 text-2xl font-bold">Scan the Barcode</h1>
        <p className="mb-6 text-slate-300">Hold the product's barcode steady in front of the camera.</p>

        <div className="relative overflow-hidden rounded-2xl border-4 border-blue-500 bg-black">
          <video ref={videoRef} className="aspect-[4/3] w-full object-cover" muted playsInline />
          {status === "scanning" && (
            <div className="pointer-events-none absolute inset-x-8 top-1/2 h-1 -translate-y-1/2 animate-pulse rounded bg-blue-400/80" />
          )}
        </div>

        <div className="mt-6 text-center">
          {status === "starting" && <p className="text-slate-300">Starting camera…</p>}
          {status === "scanning" && <p className="font-medium text-blue-300">Looking for a barcode…</p>}
          {status === "looking-up" && <p className="font-medium text-blue-300">Found a barcode — checking product…</p>}
          {status === "error" && (
            <div className="space-y-4">
              <p role="alert" className="text-red-300">{errorMessage}</p>
              <button
                type="button"
                onClick={retry}
                className="rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-700"
              >
                Try Again
              </button>
              <div>
                <Link href="/search?mode=type" className="text-sm text-blue-300 hover:underline">
                  Or type the product name instead
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
