import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedDx Assistant | Portfolio",
  description:
    "Recruiter-facing portfolio artifact for MedDx Assistant, an AI-powered clinical laboratory review and decision support capstone project.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
