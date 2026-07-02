import Image from "next/image"
import { SITE } from "@/lib/site-data"

export function SiteFooter() {
  return (
    <footer className="bg-charcoal text-ivory">
      <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
        <div className="grid gap-10 md:grid-cols-[1.2fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-olive">
                <Image
                  src="/img/logo.png"
                  alt={`Logo de ${SITE.name}`}
                  width={48}
                  height={48}
                  className="h-12 w-12 object-cover"
                />
              </span>
              <span className="font-serif text-xl">Cima Pilates</span>
            </div>
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-ivory/65">
              Estudio boutique de Pilates Reformer enfocado en el bienestar de
              la mujer. Técnica, calma y progreso en cada clase.
            </p>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-luxe text-butter">
              Estudio
            </p>
            <ul className="mt-4 space-y-2 text-sm text-ivory/75">
              <li>{SITE.location}</li>
              <li>{SITE.metro}</li>
              <li>{SITE.hoursWeek}</li>
              <li>{SITE.hoursSaturday}</li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-luxe text-butter">
              Plataforma
            </p>
            <ul className="mt-4 space-y-2 text-sm text-ivory/75">
              <li>
                <a href="#ingresar" className="hover:text-butter">
                  Ingresar
                </a>
              </li>
              <li>
                <a href="#espera" className="hover:text-butter">
                  Registrarme
                </a>
              </li>
              <li>
                <a href="#planes" className="hover:text-butter">
                  Planes y precios
                </a>
              </li>
              <li>
                <a href="#metodo" className="hover:text-butter">
                  El método
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-ivory/12 pt-6 text-xs text-ivory/50 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} {SITE.legal}. Todos los derechos reservados.</p>
          <p>Puente Alto · Región Metropolitana</p>
        </div>
      </div>
    </footer>
  )
}
