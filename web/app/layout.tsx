import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrivGuard",
  description: "Personal data exposure tracker and opt-out manager.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
