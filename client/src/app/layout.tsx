import type { Metadata } from "next";
import "./globals.css";
import Footer from "@/components/footer";
import CookieWidget from "@/components/cookie-widget";

export const metadata: Metadata = {
  title: "Parallax",
  description: "Parallax - Chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  
  return (
    <html lang="en" className="h-full">
      <head>
          <link rel="icon" href="favicon.ico" type="icon"/>
          <meta charSet="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <CookieWidget/>
      </head>
      <body className="min-h-screen flex flex-col">
        {children}
      </body>
    </html>
  );
}
