import { Analytics } from '@vercel/analytics/next'
import type { Metadata } from 'next'
import { Inter, Fraunces } from 'next/font/google'
import './globals.css'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
})
const fraunces = Fraunces({
  variable: '--font-fraunces',
  subsets: ['latin'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Cima Pilates | Estudio de Reformer en Puente Alto',
  description:
    'Cima Pilates SpA — Estudio boutique de Pilates Reformer enfocado en el bienestar de la mujer. Av. Concha y Toro 3346, Local 32, Puente Alto. Planes mensuales, trimestrales y semestrales.',
  generator: 'v0.app',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${fraunces.variable} bg-background`}
    >
      <body className="font-sans antialiased">
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
