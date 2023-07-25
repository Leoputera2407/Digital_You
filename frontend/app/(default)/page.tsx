export const metadata = {
  title: 'Prosona - Empowering Knowledge Workers',
  description: 'Prosona Landing Page',
}

import AboutUs from '@/components/ui/about-us'
import Cta from '@/components/ui/cta'
import Features02 from '@/components/ui/features-02'
import Hero from '@/components/ui/hero'
import Integrations from '@/components/ui/integrations'
import Testimonials from '@/components/ui/testimonials'

export default function Home() {
  return (
    <>
      <Hero />
       <Features02 />
       <Integrations />
      <AboutUs />
      <Testimonials />
      <Cta />
    </>
  )
}
