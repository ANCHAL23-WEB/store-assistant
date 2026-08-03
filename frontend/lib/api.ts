/** Typed client functions for the retail store assistant API. */

export interface Product {
  product_id: number;
  name: string;
  brand: string;
  price: number;
  specs: Record<string, unknown>;
  distance: number;
}

export interface ImageSearchResponse {
  products: Product[];
  message?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** Search for products semantically through the FastAPI backend. */
export async function searchProducts(
  query: string,
  topK = 10,
): Promise<Product[]> {
  const url = new URL("/search", API_URL);
  url.searchParams.set("q", query);
  url.searchParams.set("top_k", String(topK));

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Search request failed with status ${response.status}`);
  }

  return response.json() as Promise<Product[]>;
}

/** Upload an image for OCR, then return products matching its extracted text. */
export async function searchProductsByImage(image: File): Promise<ImageSearchResponse> {
  const formData = new FormData();
  formData.append("image", image);

  const response = await fetch(new URL("/ocr/search", API_URL), {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Image search request failed with status ${response.status}`);
  }

  const payload: Product[] | { results: Product[]; message?: string } = await response.json();
  return Array.isArray(payload)
    ? { products: payload }
    : { products: payload.results, message: payload.message };
}
