"use client";
import Illustration from '@/public/images/glow-top.svg';
import { motion, useScroll, useSpring, useTransform } from "framer-motion";
import Image from 'next/image';
import { useRef } from "react";
import Particles from './particles';


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
      </motion.div>
      
      <motion.video
        style={{ 
          scale: videoScale, 
          width: "105%", 
          height: "100%", 
          objectFit: "cover", 
          objectPosition: "center", 
          clipPath: "inset(0 0 0 5%)"
        }}
        className="rounded-md max-w-screen-lg shadow-lg dark:shadow-white/25 border dark:border-white/25 w-full bg-white dark:bg-black"
        src="https://user-images.githubusercontent.com/33604451/252248216-9cec7a5a-6542-433b-b4be-33b09a7372c9.mp4"
        autoPlay
        muted
        loop
      />
    </section>
  );
};

export default hero_new;
