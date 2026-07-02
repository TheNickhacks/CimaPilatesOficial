"use client"

import { useState } from "react"
import { PLANS, SITE } from "@/lib/site-data"

const PERIODS = [
  { key: "monthly", label: "Mensual", note: "" },
  { key: "quarterly", label: "Trimestral", note: "10% OFF" },
  { key: "semester", label: "Semestral", note: "hasta 12.5% OFF" },
] as const

type PeriodKey = (typeof PERIODS)[number]["key"]

export function Plans() {
  const [period, setPeriod] = useState<PeriodKey>("monthly")

  return (
    <section id="planes" className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">
      <div className="flex flex-col items-start gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-luxe text-olive-gold">
            <span className="h-px w-10 bg-olive-gold/50" />
            Planes
          </p>
          <h2 className="mt-6 max-w-2xl text-balance font-serif text-4xl font-light leading-tight text-charcoal md:text-5xl">
            Elige el plan que sigue tu ritmo
          </h2>
        </div>

        <div className="inline-flex rounded-full border border-olive/20 bg-card p-1">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              type="button"
              onClick={() => setPeriod(p.key)}
              className={`rounded-full px-5 py-2.5 text-sm font-medium transition-colors ${
                period === p.key
                  ? "bg-olive text-ivory shadow-sm"
                  : "text-charcoal/70 hover:text-olive"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {PERIODS.find((p) => p.key === period)?.note && (
        <p className="mt-5 inline-flex rounded-full bg-butter px-4 py-1.5 text-sm font-medium text-charcoal">
          {PERIODS.find((p) => p.key === period)?.note} vs. plan mensual
        </p>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan, i) => {
          const featured = i === 1
          return (
            <article
              key={plan.credits}
              className={`flex flex-col rounded-[1.75rem] border p-7 transition-transform hover:-translate-y-1 ${
                featured
                  ? "border-olive bg-olive text-ivory"
                  : "border-olive/15 bg-card text-charcoal"
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`font-serif text-4xl font-light ${
                    featured ? "text-butter" : "text-olive"
                  }`}
                >
                  {plan.icon}
                </span>
                {featured && (
                  <span className="rounded-full bg-butter px-3 py-1 text-xs font-medium text-charcoal">
                    Popular
                  </span>
                )}
              </div>
              <h3 className="mt-4 font-serif text-xl">{plan.credits}</h3>
              <p
                className={`mt-1 text-sm ${
                  featured ? "text-ivory/75" : "text-charcoal/65"
                }`}
              >
                {plan.frequency}
              </p>
              <p className="mt-6 font-serif text-3xl">{plan[period]}</p>
              <a
                href="#espera"
                className={`mt-6 rounded-full px-5 py-3 text-center text-sm font-medium transition-colors ${
                  featured
                    ? "bg-butter text-charcoal hover:bg-ivory"
                    : "bg-olive text-ivory hover:bg-olive-gold"
                }`}
              >
                Contratar
              </a>
            </article>
          )
        })}
      </div>

      <div className="mt-4 flex flex-col items-start justify-between gap-5 rounded-[1.75rem] border border-olive/15 bg-beige/40 p-7 md:flex-row md:items-center">
        <div>
          <p className="text-xs font-medium uppercase tracking-luxe text-olive-gold">
            Clase suelta
          </p>
          <h3 className="mt-2 font-serif text-2xl text-charcoal">
            Entrena sin compromiso de plan
          </h3>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-charcoal/70">
            Perfecta para conocer el estudio o asistir de manera flexible cuando
            lo necesites.
          </p>
        </div>
        <div className="flex items-center gap-5">
          <p className="font-serif text-4xl font-light text-olive">
            {SITE.singleClass}
          </p>
          <a
            href="#espera"
            className="rounded-full bg-olive-gold px-6 py-3 text-sm font-medium text-ivory transition-transform hover:-translate-y-0.5"
          >
            Reservar
          </a>
        </div>
      </div>
    </section>
  )
}
