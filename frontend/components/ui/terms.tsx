export default function Terms() {
  return (
    <section className="relative">

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

        <div className="pt-16 pb-12 md:pt-32 md:pb-20">

          {/* Section header */}
          <div className="max-w-3xl mx-auto text-left pb-12 md:pb-20">
            <h2 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60 pb-4">Terms and Conditions</h2>
           
            <div>
            <p><strong>Last Updated:</strong> 07/24/2023</p>

            <h2>Acceptance of Terms</h2>
            <p>By accessing and using the services provided by Prosona ("we", "our", "us"), you agree to be bound by these Terms and Conditions. If you disagree with any part of these Terms and Conditions, you may not access or use our services.</p>

            <h2>Changes to Terms</h2>
            <p>We reserve the right to update or change our Terms and Conditions at any time. If changes are made, we will notify you by updating the 'Last Updated' date at the top of this page. Your continued use of the Service after such changes constitutes your acceptance of the new Terms and Conditions.</p>

            <h2>Access to Services</h2>
            <p>Subject to these Terms and Conditions, we may offer you access to our services. We reserve the right to withdraw or amend the services, and any service or material we provide, in our sole discretion without notice. We will not be liable if for any reason all or any part of the service is unavailable at any time or for any period.</p>

            <h2>User Obligations</h2>
            <p>As a user, you agree not to use the service for any unlawful purpose or in any way that could damage, disable, overburden, or impair any server, or the network(s) connected to any server, or interfere with any other party's use and enjoyment of the service.</p>

            <h2>Intellectual Property</h2>
            <p>All content, features, and functionality on the service, including software, text, images, and logos are owned by Prosona, its licensors, or other providers of such material and are protected by copyright, trademark, and other intellectual property or proprietary rights laws.</p>

            <h2>Limitation of Liability</h2>
            <p>In no event will Prosona, or its suppliers or licensors be liable for any special, incidental, or consequential damages, including lost profits, lost data or confidential or other information, business interruption, personal injury, or any other pecuniary loss, arising out of the use or inability to use the services.</p>

            <h2>Indemnity</h2>
            <p>You agree to indemnify, defend and hold harmless Prosona, its officers, directors, employees, agents, and third parties, for any losses, costs, liabilities, and expenses (including reasonable attorney's fees) relating to or arising out of your use of or inability to use the Service, any user postings made by you, your violation of any terms of this Agreement or your violation of any rights of a third party, or your violation of any applicable laws, rules or regulations.</p>

            <h2>Governing Law and Jurisdiction</h2>
            <p>These Terms and Conditions shall be governed by and construed in accordance with the laws of United States, and you agree to submit to the exclusive jurisdiction of the United States courts.</p>

            <h2>Contact Us</h2>
            <p>If you have any questions about these Terms and Conditions, please contact us at hamish@prosona.ai.</p>

        </div>


          </div>

        </div>
    </section>
  )
}