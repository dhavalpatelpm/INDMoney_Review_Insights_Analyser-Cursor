import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "INDmoney Review Insights",
  description: "Weekly Review Pulse - Generate one-pager and send email",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased min-h-screen bg-[#0a1628] text-white`}>
        {/* INDMoney-style gradient mesh background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
          <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-[#00d4aa]/20 rounded-full blur-[120px]" />
          <div className="absolute top-1/2 -left-40 w-[500px] h-[500px] bg-[#6366f1]/25 rounded-full blur-[100px]" />
          <div className="absolute -bottom-40 right-1/3 w-[400px] h-[400px] bg-[#0ea5e9]/15 rounded-full blur-[100px]" />
          <div
            className="absolute inset-0 opacity-40"
            style={{
              background: "linear-gradient(180deg, transparent 0%, rgba(10,22,40,0.8) 50%, #0a1628 100%)",
            }}
          />
        </div>
        <div className="relative min-h-screen">{children}</div>
      </body>
    </html>
  );
}
