import Image from "next/image"
import { SITE } from "@/lib/site-data"

export function Visit() {
  return (
    <section id="visita" className="relative overflow-hidden">
      <Image
        src="/img/cta-studio.png"
        alt="Rincón del estudio Cima Pilates con una cama reformer y luz natural"
        fill
        className="object-cover"
      />
      <div className="absolute inset-0 bg-charcoal/72" />
      <div className="relative mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
        <div className="grid gap-10 lg:grid-cols-2">
          <div>
            <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-butter">
              <span className="h-px w-10 bg-butter/50" />
              Visítanos
            </p>
            <h2 className="mt-6 max-w-xl text-balance font-serif text-4xl font-light leading-tight text-ivory md:text-5xl">
              Te esperamos en el corazón de Puente Alto
            </h2>
            <p className="mt-6 max-w-md leading-relaxed text-ivory/80">
              {SITE.location}. A pasos del {SITE.metro}, en un local pensado
              para que llegar a tu clase sea fácil y cómodo.
            </p>
          </div>

          <div className="grid gap-4 self-center sm:grid-cols-2">
            <InfoCard title="Ubicación">
              {SITE.location}
              <span className="mt-1 block text-ivory/65">{SITE.metro}</span>
            </InfoCard>
            <InfoCard title="Lunes a viernes">
              07:00 – 12:00 hrs
              <span className="mt-1 block">16:00 – 22:00 hrs</span>
            </InfoCard>
            <InfoCard title="Sábado">09:00 – 14:00 hrs</InfoCard>
            <InfoCard title="Clase suelta">
              <span className="font-serif text-2xl text-butter">
                {SITE.singleClass}
              </span>
            </InfoCard>
          </div>
        </div>
      </div>
    </section>
  )
}

function InfoCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-[1.5rem] border border-ivory/15 bg-ivory/[0.08] p-6 backdrop-blur-sm">
      <p className="text-xs font-medium uppercase tracking-luxe text-butter">
        {title}
      </p>
      <div className="mt-3 text-sm leading-relaxed text-ivory/90">
        {children}
      </div>
    </div>
  )
}
