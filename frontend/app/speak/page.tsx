// ROUTE: /speak
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

// Minimal shape of the browser SpeechRecognition API (not yet in standard TS lib types).
interface SpeechRecognitionResultLike {
  results: { [index: number]: { [index: number]: { transcript: string } } };
}
interface SpeechRecognitionErrorLike {
  error: string;
}
interface SpeechRecognitionLike {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  onresult: ((event: SpeechRecognitionResultLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null;
  onend: (() => void) | null;
}
interface WindowWithSpeechRecognition extends Window {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
}

export default function SpeakPage() {
  const router = useRouter();
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  const [status, setStatus] = useState<"idle" | "listening" | "no-support" | "error">("idle");
  const [transcript, setTranscript] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const win = window as WindowWithSpeechRecognition;
    const SpeechRecognitionCtor = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time browser-support check on mount, not a render-loop issue
      setStatus("no-support");
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setStatus("idle");
    };

    recognition.onerror = (event) => {
      setStatus("error");
      setErrorMessage(`Could not hear you clearly (${event.error}). Please try again.`);
    };

    recognition.onend = () => {
      setStatus((prev) => (prev === "listening" ? "idle" : prev));
    };

    recognitionRef.current = recognition;
  }, []);

  function startListening() {
    if (!recognitionRef.current) return;
    setTranscript("");
    setErrorMessage("");
    setStatus("listening");
    recognitionRef.current.start();
  }

  function handleSearch() {
    if (!transcript.trim()) return;
    router.push(`/search?q=${encodeURIComponent(transcript.trim())}&input_type=voice`);
  }

  return (
    <main className="flex min-h-screen flex-col items-center bg-slate-950 px-4 py-8 text-white">
      <div className="mx-auto w-full max-w-xl text-center">
        <Link href="/" className="mb-6 inline-flex items-center gap-1 text-sm font-semibold text-blue-300 hover:underline">
          ← Back to home
        </Link>

        <h1 className="mb-2 text-2xl font-bold">Speak the Product Name</h1>
        <p className="mb-6 text-slate-300">Tap the mic and say what you&apos;re looking for.</p>

        {status === "no-support" && (
          <div className="space-y-4">
            <p role="alert" className="text-red-300">
              Voice search isn&apos;t supported in this browser. Please use Chrome, or try the Type option instead.
            </p>
            <Link href="/search" className="text-sm text-blue-300 hover:underline">
              Go to Type search
            </Link>
          </div>
        )}

        {status !== "no-support" && (
          <>
            <button
              type="button"
              onClick={startListening}
              disabled={status === "listening"}
              className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-blue-600 text-4xl hover:bg-blue-700 disabled:opacity-50"
            >
              🎤
            </button>

            <p className="mt-4 font-medium text-blue-300">
              {status === "listening" && "Listening…"}
              {status === "idle" && !transcript && "Tap to start"}
            </p>

            {status === "error" && <p role="alert" className="mt-4 text-red-300">{errorMessage}</p>}

            {transcript && (
              <div className="mt-6 space-y-4">
                <p className="text-lg">You said: <span className="font-semibold">&quot;{transcript}&quot;</span></p>
                <button
                  type="button"
                  onClick={handleSearch}
                  className="rounded-lg bg-blue-600 px-6 py-3 font-semibold hover:bg-blue-700"
                >
                  Search for this
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}