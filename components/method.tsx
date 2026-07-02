import { METHOD_STEPS } from "@/lib/site-data"

export function Method() {
  return (
    <section id="metodo" className="bg-olive text-ivory">
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <div className="lg:sticky lg:top-28">
            <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-butter">
              <span className="h-px w-10 bg-butter/50" />
              El método
            </p>
            <h2 className="mt-6 text-balance font-serif text-4xl font-light leading-tight md:text-5xl">
              Qué es el Pilates Reformer
            </h2>
            <p className="mt-6 text-pretty leading-relaxed text-ivory/80">
              El método Pilates es un sistema de ejercicio de cuerpo completo
              creado por Joseph Pilates, centrado en fortalecer la musculatura
              profunda, mejorar la postura y coordinar el movimiento con la
              respiración. El{" "}
              <span className="text-butter">reformer</span> es la cama
              especializada que lo lleva más lejos: un carro deslizante,
              resortes y poleas que generan resistencia ajustable y, a la vez,
              asistencia segura.
            </p>
            <p className="mt-4 text-pretty leading-relaxed text-ivory/80">
              El resultado es un entrenamiento exigente pero amable con tus
              articulaciones, donde cada repetición es consciente, controlada y
              guiada. No se trata de cuántas veces, sino de cómo te mueves.
            </p>
          </div>

          <div className="space-y-4">
            {METHOD_STEPS.map((item) => (
              <article
                key={item.step}
                className="rounded-[1.75rem] border border-ivory/15 bg-ivory/[0.06] p-7 transition-colors hover:bg-ivory/[0.1]"
              >
                <div className="flex items-baseline gap-5">
                  <span className="font-serif text-3xl text-butter">
                    {item.step}
                  </span>
                  <div>
                    <h3 className="font-serif text-2xl">{item.title}</h3>
                    <p className="mt-3 leading-relaxed text-ivory/75">
                      {item.text}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
