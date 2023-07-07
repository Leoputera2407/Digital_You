import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
 

interface Params<T> {
  param: T | null | undefined;
  errorText?: string;
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function verifyValidParamString<T>({ param, errorText = "Param is undefined" }: Params<T>): T {
  if (param === undefined || param === null) {
    throw new Error(errorText);
  }
  // We've already checked that param is not null or undefined, so we can assert it as T
  return param as T;
}