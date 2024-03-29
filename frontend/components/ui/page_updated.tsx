export const metadata = {
  title: 'Prosona - Empowering TikTok Creators',
  description: 'Automated content snippet pipeline for TikTok creators',
}

import AboutUs from '@/components/ui/about-us'
import Cta from '@/components/ui/cta'
import Features from '@/components/ui/features'
import Hero from '@/components/ui/hero'
import Integrations from '@/components/ui/integrations'
import Testimonials from '@/components/ui/testimonials'

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
