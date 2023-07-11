"use client";
import {
  Info,
  Lightning,
  LightningSlash,
  Plug,
  Trash,
  XSquare
} from "@phosphor-icons/react";
import { BsPeopleFill } from "react-icons/bs";
import { FaGlobe } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { SiConfluence, SiGithub, SiGoogledrive, SiJira, SiLinear, SiNotion, SiSlack } from "react-icons/si";

interface IconProps {
  size?: string;
  className?: string;
}

const defaultTailwindCSS = "my-auto flex flex-shrink-0";

export const PlugIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <Plug size={size} className={className} />;
};

export const WorkspaceIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <BsPeopleFill size={size} className={className} />;
};

export const TrashIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <Trash size={size} className={className} />;
};

export const LinkBreakIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <LightningSlash size={size} className={className} />;
};

export const LinkIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <Lightning size={size} className={className} />;
};

export const XSquareIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <XSquare size={size} className={className} />;
};

export const GlobeIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <FaGlobe size={size} className={className} />;
};

export const SlackIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiSlack size={size} className={className} />;
};

export const GithubIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiGithub size={size} className={className} />;
};

export const GoogleDriveIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiGoogledrive size={size} className={className} />;
};

export const ConfluenceIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiConfluence size={size} className={className} />;
};

export const NotionIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiNotion size={size} className={className} />;
};

export const LinearIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiLinear size={size} className={className} />;
}

export const JiraIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <SiJira size={size} className={className} />;
}

export const InfoIcon = ({
  size = "16",
  className = defaultTailwindCSS,
}: IconProps) => {
  return <Info size={size} className={className} />;
};

export const GoogleFCIcon = ({
  size = "16",
  className,
}: IconProps) => {
  return <FcGoogle size={size} className={className} />;
}