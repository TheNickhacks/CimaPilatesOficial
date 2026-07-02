import { SiteHeader } from "@/components/site-header"
import { Hero } from "@/components/hero"
import { Method } from "@/components/method"
import { Gallery } from "@/components/gallery"
import { Plans } from "@/components/plans"
import { Benefits } from "@/components/benefits"
import { Waitlist } from "@/components/waitlist"
import { Visit } from "@/components/visit"
import { SiteFooter } from "@/components/site-footer"

export default function Page() {
  return (
    <div className="min-h-screen bg-ivory">
      <SiteHeader />
      <main>
        <Hero />
        <Method />
        <Gallery />
        <Plans />
        <Benefits />
        <Waitlist />
        <Visit />
      </main>
      <SiteFooter />
    </div>
  )
}
