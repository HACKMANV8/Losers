import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IRis - ML-Guided Compiler Optimization",
  description: "AI-guided compiler optimization system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`antialiased`}>
        {children}
      </body>
    </html>
  );
}
