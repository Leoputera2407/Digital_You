export const metadata = {
  title: 'Prosona - Empowering Knowledge Workers',
  description: 'Prosona Landing Page',
}

import Hero from '@/components/hero_new'
import Features02 from '@/components/features-02'
import Integrations from '@/components/integrations'
import AboutUs from '@/components/about-us'
import Testimonials from '@/components/testimonials'
import Cta from '@/components/cta'

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
