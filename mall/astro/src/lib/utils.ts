// shadcn- och 21st-komponenternas klassfogning (valideringen 2026-10-12; ägarens besked om fria tyglar i skapandet)
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
