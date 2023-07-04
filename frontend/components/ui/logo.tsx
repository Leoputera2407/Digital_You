import LogoImg from '@/public/images/prosona_logo_transparent.png'
import Image from 'next/image'
import Link from 'next/link'

export default function Logo() {
  return (
    <Link className="block" href="/" aria-label="Prosona">
      <Image src={LogoImg} width={38} height={38} priority alt="Stellar" />
    </Link>
  )
}