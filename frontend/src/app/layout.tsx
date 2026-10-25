import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "./app-shell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NexusFlow — AI Project Planning",
  description: "Turn project ideas into structured, human-reviewed plans and artifacts.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ background: "#0a0a0f" }}>
      <body className={inter.className} style={{ background: "#0a0a0f" }}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
