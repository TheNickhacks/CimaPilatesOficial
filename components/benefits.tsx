import { BENEFITS } from "@/lib/site-data"

export function Benefits() {
  return (
    <section id="beneficios" className="bg-card">
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">
        <div className="max-w-2xl">
          <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-olive-gold">
            <span className="h-px w-10 bg-olive-gold/50" />
            Beneficios
          </p>
          <h2 className="mt-6 text-balance font-serif text-4xl font-light leading-tight text-charcoal md:text-5xl">
            Lo que tu cuerpo gana con la práctica regular
          </h2>
        </div>

        <div className="mt-10 grid gap-px overflow-hidden rounded-[1.75rem] border border-olive/12 bg-olive/12 sm:grid-cols-2 lg:grid-cols-3">
          {BENEFITS.map((b) => (
            <div key={b.title} className="bg-card p-7">
              <h3 className="font-serif text-xl text-olive">{b.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-charcoal/70">
                {b.text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
