/** Base URL for the Handwright FastAPI backend. */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** A single extracted glyph returned by the backend. */
export interface GlyphData {
  /** Unicode character this glyph represents, e.g. "A" */
  character: string;
  /** Session-scoped identifier for this glyph */
  glyph_id: string;
  /** URL to the extracted glyph image (relative to BASE_URL or absolute) */
  image_url: string;
  /** Whether the glyph was successfully segmented */
  ok: boolean;
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
export async function generateWorksheet(): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/api/worksheet/generate`, {
    method: "POST",
  });
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
 * Glyphs may still be processing; poll until all have `ok: true`.
 */
export async function getGlyphs(sessionId: string): Promise<GlyphData[]> {
  const response = await fetch(
    `${BASE_URL}/api/glyphs/${encodeURIComponent(sessionId)}`,
  );
  await expectOk(response);
  return response.json() as Promise<GlyphData[]>;
}

/**
 * Render a note using the user's handwriting font.
 * Returns a PNG image Blob that the caller can display or download.
 */
export async function renderNote(params: RenderParams): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/api/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  await expectOk(response);
  return response.blob();
}

/**
 * Trigger font generation for a session and download the resulting .ttf file.
 * Returns the font file as a Blob so the caller can offer a browser download.
 */
export async function generateFont(sessionId: string): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/api/font/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  await expectOk(response);
  return response.blob();
}
