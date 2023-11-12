export const metadata = {
  title: 'Prosona - Empowering Knowledge Workers',
  description: 'Prosona Landing Page',
}

import AboutUs from '@/components/ui/about-us-updated'
import Cta from '@/components/ui/cta-updated'
import Features from '@/components/ui/features_updated'
import Hero from '@/components/ui/hero_updated'
import Integrations from '@/components/ui/integrations-updated'

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <Integrations />
      <AboutUs />
      {/* <Testimonials /> */}
      <Cta />
    </>
  )
}
