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
        Breeze through your Slack and email inbox with <span className="bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-100 to-slate-200/60">Prosona.</span>
        </h1>
        <p className="text-base max-w-sm text-white-500 mb-5 sm:mb-5">
        Crafting precise responses, so you don't have to.
        </p>

        <div>
              <a className="btn p-4 text-slate-900 bg-gradient-to-r from-white/80 via-white to-white/80 hover:bg-white transition duration-150 ease-in-out group" href="https://9a04i53lzc4.typeform.com/to/E0H4xTzS">
                Beta Waitlist <span className="tracking-normal text-purple-500 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">-&gt;</span>
              </a>
            </div>

      </motion.div>
      
      <motion.video
        style={{ 
          scale: videoScale, 
          width: "100%", 
          height: "100%", 
          objectFit: "cover", 
          objectPosition: "center", 
          clipPath: "inset(0 0 0 0)"
        }}
        className="rounded-2xl max-w-screen-lg shadow-lg dark:shadow-white/25 border dark:border-slate/25 w-full bg-white dark:bg-black"
        src="https://user-images.githubusercontent.com/34851861/258572913-7944c2c6-ae68-4f77-abea-260c9624e838.mp4"
        autoPlay
        muted
        loop
      />
    </section>
  );
};

export default hero_new;
