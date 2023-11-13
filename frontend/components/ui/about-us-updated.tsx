export default function AboutUs() {
  return (
    <section className="relative">
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
        {/* Blurred shape */}
        <div className="absolute top-0 -mt-24 left-0 -ml-16 blur-2xl opacity-70 pointer-events-none -z-10" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" width="434" height="427">
            <defs>
              <linearGradient id="bs4-a" x1="19.609%" x2="50%" y1="14.544%" y2="100%">
                <stop offset="0%" stopColor="#A855F7" />
                <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path fill="url(#bs4-a)" fillRule="evenodd" d="m0 0 461 369-284 58z" transform="matrix(1 0 0 -1 0 427)" />
          </svg>
        </div>
        <p>
          We've pivoted to empower the TikTok creator community. Our mission is to streamline the creative 
          process by transforming long-form content into captivating TikTok snippets. With Prosona, creators 
          can effortlessly turn hours of footage into bite-sized, viral-ready videos. Our expertise lies in 
          leveraging cutting-edge technology to enhance content discoverability and engagement on TikTok.
        </p>
      </div>
    </section>
  )
}
