import Image from "next/image"
import { GALLERY } from "@/lib/site-data"

export function Gallery() {
  return (
    <section id="estudio" className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-olive-gold">
            <span className="h-px w-10 bg-olive-gold/50" />
            El estudio
          </p>
          <h2 className="mt-6 max-w-2xl text-balance font-serif text-4xl font-light leading-tight text-charcoal md:text-5xl">
            Un espacio diseñado para habitar la calma
          </h2>
        </div>
        <p className="max-w-md text-pretty leading-relaxed text-charcoal/70">
          Luz natural, materiales nobles y orden visual. Cada detalle está
          pensado para que tu única tarea sea entrenar y sentirte bien.
        </p>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {GALLERY.map((item) => (
          <article
            key={item.title}
            className="group overflow-hidden rounded-[1.75rem] border border-olive/12 bg-card"
          >
            <div className="overflow-hidden">
              <Image
                src={item.src || "/placeholder.svg"}
                alt={item.title}
                width={600}
                height={500}
                className="h-64 w-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
            </div>
            <div className="p-6">
              <h3 className="font-serif text-xl text-charcoal">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-charcoal/70">
                {item.text}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
