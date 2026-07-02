import Image from "next/image"
import { SITE } from "@/lib/site-data"

export function Hero() {
  return (
    <section id="inicio" className="relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-5 pb-10 pt-12 lg:px-8 lg:pt-20">
        <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-olive-gold">
          <span className="h-px w-10 bg-olive-gold/50" />
          {SITE.legal} · Puente Alto
        </p>

        <h1 className="mt-7 max-w-5xl text-balance font-serif text-5xl font-light leading-[0.98] tracking-tight text-charcoal sm:text-6xl md:text-7xl lg:text-8xl">
          Alcanza tu <span className="italic text-olive">cima</span> en cada
          movimiento.
        </h1>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end">
          <p className="max-w-xl text-pretty text-lg leading-relaxed text-charcoal/75">
            Un estudio boutique de Pilates Reformer pensado para la mujer que
            quiere moverse mejor, sentirse fuerte y reconectar con su cuerpo.
            Técnica real, grupos reducidos y un espacio que invita a la calma.
          </p>

          <div className="flex flex-wrap gap-3 lg:justify-end">
            <a
              href="#planes"
              className="rounded-full bg-olive px-7 py-3.5 text-sm font-medium text-ivory shadow-sm transition-transform hover:-translate-y-0.5"
            >
              Ver planes
            </a>
            <a
              href="#metodo"
              className="rounded-full border border-olive/30 px-7 py-3.5 text-sm font-medium text-olive transition-colors hover:bg-olive/5"
            >
              Conocer el método
            </a>
          </div>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-[1.4fr_1fr]">
          <div className="group relative overflow-hidden rounded-[2rem] border border-olive/10">
            <Image
              src="/img/hero-reformer.png"
              alt="Mujer practicando Pilates en una cama reformer en el estudio Cima Pilates"
              width={1200}
              height={800}
              priority
              className="h-[320px] w-full object-cover transition-transform duration-700 group-hover:scale-105 md:h-[460px]"
            />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-charcoal/55 to-transparent p-6">
              <p className="font-serif text-2xl text-ivory">
                4 camas reformer · 2 bloques horarios
              </p>
            </div>
          </div>

          <div className="grid gap-4">
            <Stat
              kpi="Reformer"
              label="Entrenamiento de bajo impacto y alta precisión sobre cama reformer profesional."
            />
            <Stat
              kpi="Mujeres"
              label="Un espacio diseñado para acompañar el bienestar femenino en cada etapa."
            />
            <Stat
              kpi="Cercanía"
              label="Grupos reducidos con seguimiento real de tu progreso, clase a clase."
            />
          </div>
        </div>
      </div>
    </section>
  )
}

function Stat({ kpi, label }: { kpi: string; label: string }) {
  return (
    <div className="flex flex-col justify-center rounded-[1.5rem] border border-olive/12 bg-card p-6">
      <p className="font-serif text-2xl text-olive">{kpi}</p>
      <p className="mt-2 text-sm leading-relaxed text-charcoal/70">{label}</p>
    </div>
  )
}
