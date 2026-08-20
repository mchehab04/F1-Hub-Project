import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F1Hub",
  description: "F1 race predictions, season overview, and standings.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
