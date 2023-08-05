"use client";
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';
import { ReactNode } from 'react';

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  });
}

type PHProviderProps = {
  children: ReactNode;
};

export function PHProvider({ children }: PHProviderProps): JSX.Element {
  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}
