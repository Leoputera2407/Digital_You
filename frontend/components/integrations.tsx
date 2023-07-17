import Confluence from '@/public/images/confluence-logo.png'
import Gdrive from '@/public/images/gdrive-logo.png'
import Github from '@/public/images/github-logo.png'
import Gmail from '@/public/images/gmail-logo.png'
import Notion from '@/public/images/notion-logo.png'
import Logo from '@/public/images/prosona_logo_transparent.png'
import Slack from '@/public/images/slack-logo.png'
import Image from 'next/image'


export default function Integrations() {
  return (
    <section className="relative">
      {/* Bottom vertical line */}
      <div className="hidden md:block absolute w-0.5 h-8 bottom-0 bg-slate-800 left-1/2 -translate-x-1/2" aria-hidden="true" />
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="py-12 md:py-20 border-t border-slate-800">
          {/* Section header */}
          <div className="max-w-3xl mx-auto text-center pb-12">
            <h2 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60 pb-4">Connect to All Stores of Knowledge</h2>
          </div>
          {/* Logo animation */}
          <div className="relative flex flex-col items-center p-16">
            {/* Blurred dots */}
            <svg className="absolute top-1/2 -translate-y-1/2" width="557" height="93" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <filter x="-50%" y="-50%" width="200%" height="200%" filterUnits="objectBoundingBox" id="hlogo-blurreddots-a">
                  <feGaussianBlur stdDeviation="2" in="SourceGraphic" />
                </filter>
                <filter x="-50%" y="-50%" width="200%" height="200%" filterUnits="objectBoundingBox" id="blurreddots-b">
                  <feGaussianBlur stdDeviation="2" in="SourceGraphic" />
                </filter>
                <filter x="-150%" y="-150%" width="400%" height="400%" filterUnits="objectBoundingBox" id="blurreddots-c">
                  <feGaussianBlur stdDeviation="6" in="SourceGraphic" />
                </filter>
                <filter x="-150%" y="-150%" width="400%" height="400%" filterUnits="objectBoundingBox" id="blurreddots-d">
                  <feGaussianBlur stdDeviation="4" in="SourceGraphic" />
                </filter>
                <filter x="-150%" y="-150%" width="400%" height="400%" filterUnits="objectBoundingBox" id="blurreddots-e">
                  <feGaussianBlur stdDeviation="4" in="SourceGraphic" />
                </filter>
                <filter x="-50%" y="-50%" width="200%" height="200%" filterUnits="objectBoundingBox" id="blurreddots-f">
                  <feGaussianBlur stdDeviation="2" in="SourceGraphic" />
                </filter>
                <filter x="-100%" y="-100%" width="300%" height="300%" filterUnits="objectBoundingBox" id="blurreddots-g">
                  <feGaussianBlur stdDeviation="4" in="SourceGraphic" />
                </filter>
                <filter x="-150%" y="-150%" width="400%" height="400%" filterUnits="objectBoundingBox" id="blurreddots-h">
                  <feGaussianBlur stdDeviation="6" in="SourceGraphic" />
                </filter>
                <filter x="-150%" y="-150%" width="400%" height="400%" filterUnits="objectBoundingBox" id="blurreddots-i">
                  <feGaussianBlur stdDeviation="4" in="SourceGraphic" />
                </filter>
                <filter x="-75%" y="-75%" width="250%" height="250%" filterUnits="objectBoundingBox" id="blurreddots-j">
                  <feGaussianBlur stdDeviation="2" in="SourceGraphic" />
                </filter>
              </defs>
              <g fill="none" fillRule="evenodd">
                <g className="fill-indigo-600" transform="translate(437 8)">
                  <circle fillOpacity=".64" filter="url(#blurreddots-a)" cx="6" cy="66" r="6" />
                  <circle fillOpacity=".32" filter="url(#blurreddots-b)" cx="90" cy="6" r="6" />
                  <circle fillOpacity=".64" filter="url(#blurreddots-c)" cx="90" cy="66" r="6" />
                  <circle fillOpacity=".32" filter="url(#blurreddots-d)" cx="6" cy="36" r="4" />
                  <circle fillOpacity=".32" filter="url(#blurreddots-e)" cx="60" cy="36" r="4" />
                  <circle fillOpacity=".64" cx="34" cy="22" r="2" />
                  <circle fillOpacity=".32" cx="34" cy="50" r="2" />
                  <circle fillOpacity=".64" cx="118" cy="22" r="2" />
                  <circle fillOpacity=".32" cx="118" cy="50" r="2" />
                </g>
                <g className="fill-indigo-600" transform="matrix(-1 0 0 1 120 8)">
                  <circle fillOpacity=".64" filter="url(#blurreddots-f)" cx="6" cy="66" r="6" />
                  <circle fillOpacity=".32" filter="url(#blurreddots-g)" cx="90" cy="6" r="6" />
                  <circle fillOpacity=".64" filter="url(#blurreddots-h)" cx="90" cy="66" r="6" />
                  <circle fillOpacity=".32" filter="url(#blurreddots-i)" cx="6" cy="36" r="4" />
                  <circle fillOpacity=".64" filter="url(#blurreddots-j)" cx="60" cy="36" r="4" />
                  <circle fillOpacity=".32" cx="34" cy="22" r="2" />
                  <circle fillOpacity=".32" cx="34" cy="50" r="2" />
                  <circle fillOpacity=".64" cx="118" cy="22" r="2" />
                  <circle fillOpacity=".32" cx="118" cy="50" r="2" />
                </g>
              </g>
            </svg>
            <div className="relative w-32 h-32 flex justify-center items-center">
              {/* Logo */}
              <Image src={Logo} width={64} height={64} alt="Prosona" />
            </div>
          </div>
          {/* Integration boxes */}
          <div className="relative max-w-xs sm:max-w-md mx-auto md:max-w-6xl grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6 mt-10 md:mt-20">
            {/* Top vertical line */}
            <div className="hidden md:block absolute w-0.5 h-8 -top-16 -mt-2 bg-slate-800 left-1/2 -translate-x-1/2" aria-hidden="true" />
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-1/2 h-0.5 bg-slate-800 right-0" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Gdrive} width={46} height={46} alt="Icon 01" />
              </div>
            </div>
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up" data-aos-delay="100">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-full h-0.5 bg-slate-800" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Notion} width={46} height={46} alt="Icon 02" />
              </div>
            </div>
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up" data-aos-delay="200">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-full h-0.5 bg-slate-800" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Confluence} width={46} height={46} alt="Icon 03" />
              </div>
            </div>
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up" data-aos-delay="300">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-full h-0.5 bg-slate-800" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Github} width={46} height={46} alt="Icon 04" />
              </div>
            </div>
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up" data-aos-delay="400">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-full h-0.5 bg-slate-800" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Slack} width={46} height={46} alt="Icon 05" />
              </div>
            </div>
            <div className="relative flex justify-center items-center bg-slate-800 aspect-square p-2" data-aos="fade-up" data-aos-delay="500">
              {/* Inner lines */}
              <div className="hidden md:block absolute inset-0 w-[calc(100%+24px)] h-6 -top-10 left-1/2 -translate-x-1/2" aria-hidden="true">
                <div className="absolute w-0.5 h-full bg-slate-800 left-1/2 -translate-x-1/2" />
                <div className="absolute w-1/2 h-0.5 bg-slate-800 left-0" />
              </div>
              {/* Circle */}
              <div className="bg-gradient-to-t from-slate-800 to-slate-900 w-20 h-20 rounded-full flex justify-center items-center">
                {/* Icon */}
                <Image src={Gmail} width={46} height={46} alt="Icon 06" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}