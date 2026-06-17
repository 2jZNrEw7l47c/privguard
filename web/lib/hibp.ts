const HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/";

export async function sha1Hex(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-1", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function checkPwnedPassword(password: string): Promise<number> {
  const hash = (await sha1Hex(password)).toUpperCase();
  const prefix = hash.slice(0, 5);
  const suffix = hash.slice(5);

  const resp = await fetch(`${HIBP_RANGE_URL}${prefix}`, {
    headers: { "Add-Padding": "true" },
  });

  if (!resp.ok) {
    throw new Error(`HIBP API error: ${resp.status}`);
  }

  const body = await resp.text();
  const lines = body.split("\r\n");

  for (const line of lines) {
    const [lineSuffix, countStr] = line.split(":");
    if (lineSuffix === suffix) {
      return parseInt(countStr, 10);
    }
  }

  return 0;
}
