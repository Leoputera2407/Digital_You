export const metadata = {
  title: 'Home - Stellar',
  description: 'Page description',
}

import Cta from '@/components/cta'
// import Features from '@/components/features'
import Features02 from '@/components/features-02'
import Features04 from '@/components/features-04'
import Hero from '@/components/hero_new'
import Testimonials from '@/components/testimonials'

export default function Home() {
  return (
    <>
      <Hero />
       <Features02 />
      {/*
      <Features />
      <Features03 />
      <TestimonialsCarousel />
    <Pricing /> */}
    <Features04 />
      <Testimonials />
      <Cta />
    </>
  )
}
