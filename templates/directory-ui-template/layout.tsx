import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from '@/components/layout/navigation'
import { Footer } from '@/components/layout/footer'

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'Tech Stack Directory - Discover Tools Used by Top Creators',
  description: 'Discover the tools, software, and technology stacks used by successful creators, developers, and entrepreneurs across social media. Find inspiration for your own tech stack.',
  keywords: 'tech stack, developer tools, creator tools, software tools, productivity, design tools, ai tools, development, marketing tools',
  authors: [{ name: 'Tech Stack Directory' }],
  creator: 'Tech Stack Directory',
  publisher: 'Tech Stack Directory',
  metadataBase: new URL('https://techstack.directory'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: 'Tech Stack Directory - Discover Tools Used by Top Creators',
    description: 'Discover the tools and technology stacks used by successful creators, developers, and entrepreneurs.',
    url: 'https://techstack.directory',
    siteName: 'Tech Stack Directory',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Tech Stack Directory',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tech Stack Directory - Discover Tools Used by Top Creators',
    description: 'Discover the tools and technology stacks used by successful creators, developers, and entrepreneurs.',
    images: ['/og-image.jpg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#2563eb" />

        {/* Structured Data for SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              "name": "Tech Stack Directory",
              "description": "Discover the tools and technology stacks used by successful creators, developers, and entrepreneurs",
              "url": "https://techstack.directory",
              "potentialAction": {
                "@type": "SearchAction",
                "target": "https://techstack.directory/search?q={search_term_string}",
                "query-input": "required name=search_term_string"
              }
            })
          }}
        />
      </head>
      <body className={`${inter.className} min-h-screen flex flex-col bg-gray-50`}>
        <Navigation />
        <main className="flex-grow">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
