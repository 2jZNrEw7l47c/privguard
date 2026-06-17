import { describe, it, expect, vi, beforeEach } from "vitest";
import { sha1Hex, checkPwnedPassword } from "../lib/hibp";

describe("sha1Hex", () => {
  it("hashes 'password' to known SHA-1", async () => {
    const hash = await sha1Hex("password");
    expect(hash.toUpperCase()).toBe(
      "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8"
    );
  });

  it("hashes empty string to known SHA-1", async () => {
    const hash = await sha1Hex("");
    expect(hash.toUpperCase()).toBe(
      "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
    );
  });
});

describe("checkPwnedPassword", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("returns count > 0 when suffix found in response", async () => {
    const hashOfPassword = "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8";
    const suffix = hashOfPassword.slice(5);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => `${suffix}:42\r\nABCDE12345678901234567890123456789:1`,
      })
    );

    const count = await checkPwnedPassword("password");
    expect(count).toBe(42);
  });

  it("returns 0 when suffix not in response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => "ABCDE12345678901234567890123456789:1",
      })
    );

    const count = await checkPwnedPassword("password");
    expect(count).toBe(0);
  });

  it("throws when HIBP API is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network error"))
    );

    await expect(checkPwnedPassword("password")).rejects.toThrow();
  });
});
