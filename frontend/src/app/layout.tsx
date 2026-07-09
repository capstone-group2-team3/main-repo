import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedDx Assistant | Clinical Review Dashboard",
  description: "Doctor-facing emergency and lab report dashboard.",
  icons: {
    icon: [{ url: "/icon", type: "image/png" }],
    apple: [{ url: "/icon", type: "image/png" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
