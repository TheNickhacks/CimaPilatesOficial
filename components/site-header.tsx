"use client"

import Image from "next/image"
import { useState } from "react"
import { SITE } from "@/lib/site-data"

const NAV = [
  { label: "Método", href: "#metodo" },
  { label: "Estudio", href: "#estudio" },
  { label: "Planes", href: "#planes" },
  { label: "Beneficios", href: "#beneficios" },
  { label: "Visítanos", href: "#visita" },
]

export function SiteHeader() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-olive/15 bg-ivory/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3 lg:px-8">
        <a href="#inicio" className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-full bg-olive">
            <Image
              src="/img/logo.png"
              alt={`Logo de ${SITE.name}`}
              width={44}
              height={44}
              className="h-11 w-11 object-cover"
            />
          </span>
          <span className="font-serif text-lg leading-none tracking-tight text-olive-gold">
            Cima<span className="text-charcoal"> Pilates</span>
          </span>
        </a>

        <nav className="hidden items-center gap-8 text-sm font-medium text-charcoal/80 lg:flex">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="transition-colors hover:text-olive"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <a
            href="#ingresar"
            className="rounded-full border border-olive/30 px-5 py-2.5 text-sm font-medium text-olive transition-colors hover:bg-olive/5"
          >
            Ingresar
          </a>
          <a
            href="#espera"
            className="rounded-full bg-olive px-5 py-2.5 text-sm font-medium text-ivory shadow-sm transition-transform hover:-translate-y-0.5"
          >
            Lista de espera
          </a>
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-olive/30 text-olive lg:hidden"
          aria-label="Abrir menú"
          aria-expanded={open}
        >
          <div className="space-y-1.5">
            <span className="block h-0.5 w-5 bg-current" />
            <span className="block h-0.5 w-5 bg-current" />
          </div>
        </button>
      </div>

      {open && (
        <div className="border-t border-olive/15 bg-ivory px-5 py-4 lg:hidden">
          <nav className="flex flex-col gap-1">
            {NAV.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-xl px-3 py-2.5 text-sm font-medium text-charcoal/80 hover:bg-olive/5"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 flex gap-2">
              <a
                href="#ingresar"
                onClick={() => setOpen(false)}
                className="flex-1 rounded-full border border-olive/30 px-4 py-2.5 text-center text-sm font-medium text-olive"
              >
                Ingresar
              </a>
              <a
                href="#espera"
                onClick={() => setOpen(false)}
                className="flex-1 rounded-full bg-olive px-4 py-2.5 text-center text-sm font-medium text-ivory"
              >
                Lista de espera
              </a>
            </div>
          </nav>
        </div>
      )}
    </header>
  )
}
