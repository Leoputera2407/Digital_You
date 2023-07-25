export default function PrivacyPolicy() {
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
            <h2 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60 pb-4">Privacy Policy</h2>
            <div>
              <p><strong>Last Updated:</strong> 07/24/2023</p>
              <p>This Privacy Policy describes how Prosona ("we", "our", or "us") collects, uses, and discloses your personal information when you use our services through our website or any associated applications (collectively, the "Services").</p>

              <h2>1. Information We Collect</h2>

              <p>We collect and process the following types of information:</p>

              <ul>
                <li><strong>Personal Information:</strong> This is information that directly identifies you or could reasonably be used in combination with other information to identify you and includes such things as your name, email address, and phone number. This information is collected when you register, create an account or use our Services.</li>
                <li><strong>Usage Data:</strong> We automatically collect information on how you interact with our Services, such as the pages you visit, the frequency of access, how much time you spend on each page, what you click on, and when you use the Services.</li>
                <li><strong>Technical Data:</strong> We collect information from your devices (computers, mobile phones, tablets, etc.) such as IP addresses, browser types, log information, device information, time zone, and operating system.</li>
              </ul>

              <h2>2. Use of Information</h2>

              <p>We use the information we collect for various purposes, including to:</p>

              <ul>
                <li>Provide, maintain and improve our Services.</li>
                <li>Respond to your questions and provide user support.</li>
                <li>Understand and analyze how you use our Services and develop new products, services, features, and functionality.</li>
                <li>Communicate with you about your use of our Services and any updates or changes.</li>
                <li>Detect, prevent, or address technical or security issues.</li>
              </ul>

              <h2>3. Protection of Information</h2>

              <p>We implement a variety of security measures to help keep your information secure, such as encryption and access controls. We also review our information collection, storage, and processing practices, including physical security measures, to guard against unauthorized access to systems.</p>

              <h2>4. Sharing of Information</h2>

              <p>We do not sell or rent your personal data to marketers or third parties. However, we may share your information with trusted third parties in the following circumstances:</p>

              <ul>
                <li><strong>Service Providers:</strong> We may share your information with third-party vendors, service providers, contractors, or agents who perform services for us or on our behalf and require access to such information to do that work.</li>
                <li><strong>Legal Compliance:</strong> We may disclose your information if required to do so by law or in the good faith belief that such action is necessary to comply with a legal obligation.</li>
              </ul>

              <h2>5. Cookies</h2>

              <p>We use cookies and similar tracking technologies to track the activity on our Services and store certain information. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.</p>

              <h2>6. Your Rights</h2>

              <p>Depending on where you live, you may have certain rights with respect to your information, such as rights of access, to receive a copy of your data, to rectify your data, to erase your data, and to object to or restrict processing of your data.</p>

              <h2>7. Children's Privacy</h2>

              <p>Our Services are not directed to children under 13 (or other age as required by local law), and we do not knowingly collect personal information from children.</p>

              <h2>8. Changes to This Privacy Policy</h2>

              <p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date at the top.</p>

              <h2>9. Contact Us</h2>

              <p>If you have any questions about this Privacy Policy or our practices, please contact us at:</p>

              <p>Prosona<br />
              hamish@prosona.ai<br />
              +14156106564
              </p>

            </div>
          </div>

        </div>
    </section>
  )
}