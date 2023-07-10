"use client";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarNavProps extends React.HTMLAttributes<HTMLElement> {
  items: {
    href: string;
    title: string;
    icon: JSX.Element;
  }[];
}

export function SidebarNav({ className, items, ...props }: SidebarNavProps) {
  const pathname = usePathname();


  return (
    <nav
      className={cn(
        "flex space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1",
        className
      )}
      {...props}
    >
      {items.map((item) => (
        <Link key={item.href} href={item.href}>
           <div
            className={cn(
              "flex items-center space-x-2 px-2 py-1 rounded-lg mr-2",
              pathname === item.href
                ? "bg-gray-300 bg-opacity-20 hover:bg-gray-300 hover:bg-opacity-20"
                : "hover:bg-transparent hover:underline",
              "justify-start cursor-pointer"
            )}
          >
            {item.icon}
            <span>{item.title}</span>
          </div>
        </Link>
      ))}
    </nav>
  );
}
