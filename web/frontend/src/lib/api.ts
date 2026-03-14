/** Base URL for the Handwright FastAPI backend. */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** A single extracted glyph returned by the backend. */
export interface GlyphData {
  /** Label for this glyph, e.g. "a_1" */
  label: string;
  /** URL to the extracted glyph image (relative to API) */
  image_url: string;
  /** Width of the glyph image in pixels */
  width: number;
  /** Height of the glyph image in pixels */
  height: number;
}

/** Response from the glyphs extraction endpoint. */
export interface GlyphsResponse {
  session_id: string;
  glyph_count: number;
  glyphs: GlyphData[];
}

/** Parameters for the note-rendering endpoint. */
export interface RenderParams {
  /** The session that owns the font glyphs */
  session_id: string;
  /** Text to render in the user's handwriting */
  text: string;
  /** Output image width in pixels (default 800) */
  width?: number;
  /** Font size in points (default 48) */
  font_size?: number;
  /** Line spacing multiplier (default 1.5) */
  line_spacing?: number;
}

/** Response from the render endpoint. */
export interface RenderResponse {
  image_url: string;
  width: number;
  height: number;
}

/** Response from the font generation endpoint. */
export interface FontGenerateResponse {
  download_url: string;
  woff2_url: string;
  css_snippet: string;
  glyph_count: number;
  variant_count: number;
}

/** Upload response returned after a worksheet image is submitted. */
export interface UploadResponse {
  session_id: string;
  filename: string;
  size_bytes: string;
}

class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function expectOk(response: Response): Promise<Response> {
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(response.status, body || response.statusText);
  }
  return response;
}

/**
 * Request a blank handwriting worksheet PDF from the backend.
 * Returns the raw PDF Blob so the caller can trigger a browser download.
 */
export async function generateWorksheet(
  includeSymbols = false,
): Promise<Blob> {
  const url = new URL(`${BASE_URL}/api/worksheet/generate`);
  if (includeSymbols) url.searchParams.set("include_symbols", "true");

  const response = await fetch(url.toString(), { method: "POST" });
  await expectOk(response);
  return response.blob();
}

/**
 * Upload a worksheet image (photo or scan) and begin glyph extraction.
 * Returns a session ID that must be passed to subsequent calls.
 */
export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${BASE_URL}/api/upload`, {
    method: "POST",
    body: form,
  });
  await expectOk(response);
  return response.json() as Promise<UploadResponse>;
}

/**
 * Retrieve all glyphs associated with a session.
 * Returns the full response including session_id, glyph_count, and glyphs array.
 */
export async function getGlyphs(sessionId: string): Promise<GlyphsResponse> {
  const response = await fetch(
    `${BASE_URL}/api/glyphs/${encodeURIComponent(sessionId)}`,
  );
  await expectOk(response);
  return response.json() as Promise<GlyphsResponse>;
}

/**
 * Render a note using the user's handwriting font.
 * Returns JSON with image_url, width, and height.
 */
export async function renderNote(
  params: RenderParams,
): Promise<RenderResponse> {
  const response = await fetch(`${BASE_URL}/api/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  await expectOk(response);
  return response.json() as Promise<RenderResponse>;
}

/**
 * Preview text rendered in the user's handwriting font.
 * Convenience wrapper around renderNote with sensible defaults.
 */
export async function previewText(params: {
  text: string;
  session_id: string;
  font_size?: number;
  line_spacing?: number;
}): Promise<RenderResponse> {
  const response = await fetch(`${BASE_URL}/api/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: params.text,
      session_id: params.session_id,
      font_size: params.font_size ?? 48,
      line_spacing: params.line_spacing ?? 1.5,
    }),
  });
  if (!response.ok) throw new Error(`Render failed: ${response.status}`);
  return response.json() as Promise<RenderResponse>;
}

/**
 * Trigger font generation for a session.
 * Returns JSON with download URLs and metadata.
 */
export async function generateFont(
  sessionId: string,
  familyName: string,
  designer?: string,
): Promise<FontGenerateResponse> {
  const response = await fetch(`${BASE_URL}/api/font/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      family_name: familyName,
      designer: designer ?? "",
    }),
  });
  await expectOk(response);
  return response.json() as Promise<FontGenerateResponse>;
}
