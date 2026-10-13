import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/ui/Sidebar";

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
          <div className="flex min-h-dvh flex-col md:h-dvh md:flex-row" style={{ background: "var(--bg-base)" }}>
            <Sidebar />
            <main className="min-h-0 min-w-0 flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
