import "@testing-library/jest-dom";
import { webcrypto } from "node:crypto";
if (typeof globalThis.crypto === "undefined") {
  Object.defineProperty(globalThis, "crypto", { value: webcrypto });
}
