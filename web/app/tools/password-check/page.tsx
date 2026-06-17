import { PasswordChecker } from "@/components/PasswordChecker";

export default function PasswordCheckPage() {
  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-100">Password Breach Check</h1>
        <p className="mt-1 text-sm text-muted">
          Powered by{" "}
          <a
            href="https://haveibeenpwned.com/Passwords"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Have I Been Pwned Pwned Passwords
          </a>
          . Free to use, no API key required.
        </p>
      </div>

      <PasswordChecker />

      <div className="rounded-lg border border-border bg-panel p-4 text-xs text-muted space-y-2">
        <p>
          <strong className="text-gray-400">How it works:</strong> Your password
          is hashed (SHA-1) in your browser. Only the first 5 characters of the
          hash are sent to HIBP. The rest is compared locally — your full
          password never leaves your device.
        </p>
        <p>
          This technique is called{" "}
          <a
            href="https://en.wikipedia.org/wiki/K-anonymity"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            k-anonymity
          </a>
          . It was designed by Troy Hunt and Cloudflare.
        </p>
      </div>
    </div>
  );
}
