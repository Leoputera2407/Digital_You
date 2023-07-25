import Logo from './logo'

export default function Footer() {
  return (
    <footer>
      <div className="max-w-6xl pb-5 mx-auto px-4 sm:px-6">
          {/* 1st block */}
          <div className="sm:col-span-12 lg:col-span-4 order-1 lg:order-none">
            <div className="h-full flex flex-col sm:flex-row lg:flex-col justify-between items-center">
              <div className="mb-4 sm:mb-0 text-center">
                <div className="mb-4 flex justify-center">
                  <Logo />
                </div>
              {/* Social links */}
              <ul className="flex justify-center">
                <li>
                  <a className="flex justify-center items-center text-purple-500 hover:text-purple-400 transition duration-150 ease-in-out" href="https://twitter.com/ProsonaAi" aria-label="Twitter">
                    <svg className="w-8 h-8 fill-current" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                      <path d="M24 11.5c-.6.3-1.2.4-1.9.5.7-.4 1.2-1 1.4-1.8-.6.4-1.3.6-2.1.8-.6-.6-1.5-1-2.4-1-1.7 0-3.2 1.5-3.2 3.3 0 .3 0 .5.1.7-2.7-.1-5.2-1.4-6.8-3.4-.3.5-.4 1-.4 1.7 0 1.1.6 2.1 1.5 2.7-.5 0-1-.2-1.5-.4 0 1.6 1.1 2.9 2.6 3.2-.3.1-.6.1-.9.1-.2 0-.4 0-.6-.1.4 1.3 1.6 2.3 3.1 2.3-1.1.9-2.5 1.4-4.1 1.4H8c1.5.9 3.2 1.5 5 1.5 6 0 9.3-5 9.3-9.3v-.4c.7-.5 1.3-1.1 1.7-1.8z" />
                    </svg>
                  </a>
                </li>
              </ul>
                <div className="text-sm text-slate-300">© Prosona.ai <span className="text-slate-500">-</span> All rights reserved.  
                <span className="text-slate-500">-</span>
                    <a href="/terms"> Terms and Conditions </a> 
                    <span className="text-slate-500">-</span>
                    <a href="/privacy"> Privacy Policy </a> 
                 </div>
              </div>
            </div>
          </div>
        </div>

    </footer>
  )
}
