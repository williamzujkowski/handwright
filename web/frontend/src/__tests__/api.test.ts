import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

import {
  generateFont,
  generateWorksheet,
  getGlyphs,
  previewText,
  uploadImage,
} from "@/lib/api";

describe("API client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("generateWorksheet", () => {
    it("calls POST /api/worksheet/generate", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(["pdf"])),
      });

      await generateWorksheet();

      expect(mockFetch).toHaveBeenCalledOnce();
      const [url, opts] = mockFetch.mock.calls[0];
      expect(url.toString()).toContain("/api/worksheet/generate");
      expect(opts.method).toBe("POST");
    });

    it("passes include_symbols param when true", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(["pdf"])),
      });

      await generateWorksheet(true);

      const [url] = mockFetch.mock.calls[0];
      expect(url.toString()).toContain("include_symbols=true");
    });
  });

  describe("uploadImage", () => {
    it("sends FormData with the file", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            session_id: "abc123",
            filename: "test.png",
            size_bytes: "1024",
          }),
      });

      const file = new File(["content"], "test.png", { type: "image/png" });
      const result = await uploadImage(file);

      expect(result.session_id).toBe("abc123");
      const [, opts] = mockFetch.mock.calls[0];
      expect(opts.body).toBeInstanceOf(FormData);
    });

    it("throws on non-OK response", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 422,
        statusText: "Unprocessable Entity",
        text: () => Promise.resolve("Invalid file"),
      });

      const file = new File(["content"], "test.png", { type: "image/png" });
      await expect(uploadImage(file)).rejects.toThrow();
    });
  });

  describe("getGlyphs", () => {
    it("calls GET /api/glyphs/{sessionId}", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            session_id: "abc",
            glyph_count: 2,
            glyphs: [],
          }),
      });

      await getGlyphs("abc");

      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain("/api/glyphs/abc");
    });
  });

  describe("generateFont", () => {
    it("sends JSON with session_id and family_name", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            download_url: "/api/fonts/abc.ttf",
            woff2_url: "/api/fonts/abc.woff2",
            css_snippet: "@font-face {}",
            glyph_count: 26,
            variant_count: 52,
          }),
      });

      const result = await generateFont("abc", "Test Font", "Jane");

      expect(result.glyph_count).toBe(26);
      const [, opts] = mockFetch.mock.calls[0];
      const body = JSON.parse(opts.body);
      expect(body.session_id).toBe("abc");
      expect(body.family_name).toBe("Test Font");
      expect(body.designer).toBe("Jane");
    });
  });

  describe("previewText", () => {
    it("sends render request with defaults", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            image_url: "/api/renders/test.png",
            width: 800,
            height: 200,
          }),
      });

      const result = await previewText({
        text: "Hello",
        session_id: "abc",
      });

      expect(result.width).toBe(800);
      const [, opts] = mockFetch.mock.calls[0];
      const body = JSON.parse(opts.body);
      expect(body.font_size).toBe(48);
      expect(body.line_spacing).toBe(1.5);
    });
  });
});
