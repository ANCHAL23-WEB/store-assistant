/** Typed client functions for the retail store assistant API. */

export interface Product {
  product_id: number;
  name: string;
  brand: string;
  price: number;
  specs: Record<string, unknown>;
  distance: number;
}

export interface InventoryRecord {
  store_id: number;
  store_name: string;
  location: string;
  city: string;
  stock_qty: number;
  restock_eta_days: number | null;
}

export interface ProductDetail {
  product_id: number;
  name: string;
  category_id: number;
  category: string;
  brand: string;
  price: number;
  colors: string[];
  specs: Record<string, unknown>;
  image_url: string | null;
  barcode?: string;
  inventory: InventoryRecord[];
}

export interface PriceMatchResponse {
  approved: boolean;
  store_price: number;
  competitor_price: number;
  discount_applied: number;
  final_price: number;
  reason: string;
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

/** Fetch full product detail (price, specs, per-store inventory) by product ID. */
export async function fetchProductById(productId: number): Promise<ProductDetail> {
  const response = await fetch(new URL(`/products/${productId}`, API_URL), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Product lookup failed with status ${response.status}`);
  }
  return response.json() as Promise<ProductDetail>;
}

/** Fetch full product detail by a scanned barcode. */
export async function fetchProductByBarcode(barcode: string): Promise<ProductDetail> {
  const response = await fetch(new URL(`/products/barcode/${barcode}`, API_URL), {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Barcode lookup failed with status ${response.status}`);
  }
  return response.json() as Promise<ProductDetail>;
}

/** Evaluate and log a competitor price-match request for one product. */
export async function checkPriceMatch(options: {
  productId: number;
  storeId: number;
  competitorPrice: number;
  source: string;
}): Promise<PriceMatchResponse> {
  const response = await fetch(new URL("/price-match", API_URL), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_id: options.productId,
      store_id: options.storeId,
      competitor_price: options.competitorPrice,
      source: options.source,
    }),
  });
  if (!response.ok) {
    throw new Error(`Price match request failed with status ${response.status}`);
  }
  return response.json() as Promise<PriceMatchResponse>;
}
