import Image, { StaticImageData } from 'next/image';
import Highlighter, { HighlighterItem } from './highlighter';
import Particles from './particles';

import FeatureImg04 from '@/public/images/book-copy.png';
import FeatureImg05 from '@/public/images/briefcase.png';
import FeatureImg06 from '@/public/images/chart-connected.png';
import FeatureImg03 from '@/public/images/chart-tree.png';
import FeatureImg01 from '@/public/images/portrait.png';
import FeatureImg02 from '@/public/images/time-fast.png';

interface FeatureBoxProps {
  title: string;
  description: string;
  imageSrc: StaticImageData;
  imageAlt: string;
}

const FeatureBox: React.FC<FeatureBoxProps> = ({ title, description, imageSrc, imageAlt }) => (
  <div className="md:col-span-1" data-aos="fade-down">
    <HighlighterItem>
      <div className="relative h-full bg-slate-900 rounded-[inherit] z-20 overflow-hidden">
        <div className="flex flex-col h-full">
          { /* Radial gradient */}
          <div className="absolute bottom-0 translate-y-1/2 left-1/2 -translate-x-1/2 pointer-events-none -z-10 w-1/2 aspect-square" aria-hidden="true">
            <div className="absolute inset-0 translate-z-0 bg-slate-800 rounded-full blur-[80px]" />
          </div>
          { /* Text */}
          <div className="md:max-w-[480px] shrink-0 order-1 md:order-none p-6 pt-0 md:p-8 md:pr-0 flex-grow">
            <div>
              <h3 className="inline-flex text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60 pb-1 overflow-hidden">{title}</h3>
              <p className="text-slate-400 overflow-hidden h-24 leading-6 flex items-end">
                <span className="block overflow-hidden">{description}</span>
              </p>
            </div>
          </div>
          { /* Image */}
          <div className="relative w-full h-64 md:h-auto overflow-hidden md:pb-8">
            <Image className="absolute bottom-0 left-1/2 -translate-x-1/2 mx-auto max-w-none md:max-w-full md:relative md:left-0 md:translate-x-0" src={imageSrc} width={60} height={60} alt={imageAlt} />
          </div>
        </div>
      </div>
    </HighlighterItem>
  </div>
)


export default function Features02() {
  return (
    <section className="relative">
      

      { /* Particles animation */}
      <div className="absolute left-1/2 -translate-x-1/2 top-0 -z-10 w-80 h-80 -mt-24 -ml-32">
        <Particles className="absolute inset-0 -z-10" quantity={6} staticity={30} />    
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="pt-16 md:pt-32">

          { /* Section header */}
          <div className="max-w-3xl mx-auto text-center pb-12 md:pb-20">
            <h2 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60 pb-4">Faster. Smarter.</h2>
          </div>

          { /* Highlighted boxes */}
          <div className="relative pb-12 md:pb-20">
            { /* Blurred shape */}
            <div className="absolute bottom-0 -mb-20 left-1/2 -translate-x-1/2 blur-2xl opacity-50 pointer-events-none" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="434" height="427">
                <defs>
                  <linearGradient id="bs2-a" x1="19.609%" x2="50%" y1="14.544%" y2="100%">
                    <stop offset="0%" stopColor="#6366F1" />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path fill="url(#bs2-a)" fillRule="evenodd" d="m346 898 461 369-284 58z" transform="translate(-346 -898)" />
              </svg>
            </div>
            { /* Grid */}
            <Highlighter className="grid md:grid-cols-3 gap-6 group grid-auto-rows minmax(100px, auto)">
          <FeatureBox 
          title="Augmenting Employees"
          description="Prosona augments domain experts within a company by reducing their time spent on routine queries, allowing them to focus on their core responsibilities."
          imageSrc={FeatureImg01}
          imageAlt="Augmenting Employees"
        />
        <FeatureBox 
          title="Wildly Smart"
          description="Prosona blend the best of Vector and Keyword search to with sophisticated re-ranking to provide the most relevant results in seconds."            
          imageSrc={FeatureImg02}
          imageAlt="Wildly Smart"
        />
        <FeatureBox 
          title="Scalability and Efficiency"
          description="Prosona reduces knowledge transfer costs, thereby boosting overall productivity and scaling effectively with your business."
          imageSrc={FeatureImg03}
          imageAlt="Scalability and Efficiency"
        />
        <FeatureBox 
          title="Promotes Documentation"
          description="The tool promotes documentation, ensuring vital knowledge is preserved even when an employee leaves the company."
          imageSrc={FeatureImg04}
          imageAlt="Promotes Documentation"
        />          
        <FeatureBox 
        title="Enhanced Accountability"
        description="Prosona increases accountability by enabling domain experts to oversee the knowledge shared, preventing the spread of outdated or incorrect information."
        imageSrc={FeatureImg05}
        imageAlt="Enhanced Accountability"
      />
      <FeatureBox 
        title="Hassle-free Integration"
        description="Prosona offers a seamless integration experience, eliminating the complexities and risks associated with in-house AI tool development."
        imageSrc={FeatureImg06}
        imageAlt="Hassle-free Integration"
      />
        </Highlighter>
      </div>

        </div>
      </div>
    </section>
  )
}