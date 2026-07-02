"use client"

import { useState } from "react"

export function Waitlist() {
  const [sent, setSent] = useState(false)

  return (
    <section id="espera" className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">
      <div className="grid overflow-hidden rounded-[2rem] border border-olive/12 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="bg-olive-gold p-8 text-ivory md:p-10">
          <p className="text-xs font-medium uppercase tracking-luxe text-butter">
            Lista de espera
          </p>
          <h2 className="mt-5 font-serif text-3xl font-light leading-tight md:text-4xl">
            Acceso anticipado para nuevas alumnas
          </h2>
          <p className="mt-5 leading-relaxed text-ivory/80">
            Déjanos tus datos y te contactaremos para priorizar tu cupo,
            avisarte de aperturas de agenda y compartirte novedades del estudio
            antes que nadie.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-ivory/85">
            {[
              "Registro preferencial en la plataforma",
              "Prioridad en los bloques de mayor demanda",
              "Promociones de lanzamiento exclusivas",
            ].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="h-1.5 w-1.5 rounded-full bg-butter" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-card p-8 md:p-10">
          {sent ? (
            <div className="flex h-full flex-col items-start justify-center">
              <h3 className="font-serif text-2xl text-olive">
                ¡Gracias por sumarte!
              </h3>
              <p className="mt-3 leading-relaxed text-charcoal/70">
                Hemos recibido tus datos. Te contactaremos muy pronto para
                coordinar tu ingreso a Cima Pilates.
              </p>
            </div>
          ) : (
            <form
              className="space-y-5"
              onSubmit={(e) => {
                e.preventDefault()
                setSent(true)
              }}
            >
              <Field label="Nombre completo" id="name" placeholder="Tu nombre" />
              <Field
                label="Correo electrónico"
                id="email"
                type="email"
                placeholder="tucorreo@email.com"
              />
              <Field
                label="Teléfono"
                id="phone"
                type="tel"
                placeholder="+56 9 ..."
              />
              <button
                type="submit"
                className="w-full rounded-full bg-olive px-6 py-3.5 text-sm font-medium text-ivory transition-transform hover:-translate-y-0.5"
              >
                Unirme a la lista de espera
              </button>
              <p className="text-xs leading-relaxed text-charcoal/55">
                Tus datos se usan solo para contacto comercial de Cima Pilates
                SpA y se almacenan de forma confidencial.
              </p>
            </form>
          )}
        </div>
      </div>
    </section>
  )
}

function Field({
  label,
  id,
  type = "text",
  placeholder,
}: {
  label: string
  id: string
  type?: string
  placeholder?: string
}) {
  return (
    <div className="grid gap-2">
      <label htmlFor={id} className="text-sm font-medium text-charcoal">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        required
        placeholder={placeholder}
        className="rounded-2xl border border-olive/20 bg-ivory/70 px-4 py-3 text-charcoal outline-none transition focus:border-olive focus:ring-4 focus:ring-olive/10"
      />
    </div>
  )
}
