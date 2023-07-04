"use client";
import Illustration from '@/public/images/glow-top.svg';
import { motion, useScroll, useSpring, useTransform } from "framer-motion";
import Image from 'next/image';
import Link from "next/link";
import Particles from './particles'
import { useRef } from "react";
import { MdNorthEast } from "react-icons/md";

import Button from "../lib/Button";

const hero_new = (): JSX.Element => {
  const targetRef = useRef<HTMLDivElement | null>(null);
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ["start start", "end start"],
  });

  const scaleSync = useTransform(scrollYProgress, [0, 0.5], [1, 0.9]);
  const scale = useSpring(scaleSync, { mass: 0.1, stiffness: 100 });

  const position = useTransform(scrollYProgress, (pos) => {
    if (pos === 1) {
      return "relative";
    }

    return "sticky";
  });

  const videoScaleSync = useTransform(scrollYProgress, [0, 0.5], [0.9, 1]);
  const videoScale = useSpring(videoScaleSync, { mass: 0.1, stiffness: 100 });

  const opacitySync = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const opacity = useSpring(opacitySync, { mass: 0.1, stiffness: 200 });

  return (
    
    <section
      ref={targetRef}
      className="relative w-full flex flex-col gap-24 items-center text-center min-h-[768px] py-12"
    >
              { /* Particles animation */}
        <Particles className="absolute inset-0 -z-10" />

              { /* Illustration */}
        <div className="absolute inset-0 -z-10 -mx-28 rounded-t-[3rem] pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute left-1/2 -translate-x-1/2 top-0 -z-10">
            <Image src={Illustration} className="max-w-none" width={1404} height={658} alt="Features Illustration" />
          </div>
        </div>
        
      <motion.div
        style={{ scale, opacity, position }}
        className="top-24 -z-0 flex flex-col gap-2 items-center justify-center pt-24"
      >
        <h1 className="text-5xl sm:text-6xl font-bold max-w-lg sm:max-w-xl">
        Empowering Experts, Powering Knowledge. <span className="text-primary">Prosona.</span>
        </h1>
        <p className="text-base max-w-sm text-gray-500 mb-5 sm:mb-10">
        Your Personalized Workplace Co-Pilot, Amplifying Your Professional Impact.
        </p>
        <div>
              <a className="btn text-slate-900 bg-gradient-to-r from-white/80 via-white to-white/80 hover:bg-white transition duration-150 ease-in-out group" href="#0">
                Beta Sign Up <span className="tracking-normal text-purple-500 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">-&gt;</span>
              </a>
            </div>
        <Link target="_blank" href={"https://github.com/StanGirard/quivr/"}>
          <Button variant={"tertiary"}>
            Github <MdNorthEast />
          </Button>
        </Link>
      </motion.div>
      <motion.video
        style={{ scale: videoScale }}
        className="rounded-md max-w-screen-lg shadow-lg dark:shadow-white/25 border dark:border-white/25 w-full bg-white dark:bg-black"
        src="https://user-images.githubusercontent.com/19614572/238774100-80721777-2313-468f-b75e-09379f694653.mp4"
        autoPlay
        muted
        loop
      />
    </section>
  );
};

export default hero_new;
