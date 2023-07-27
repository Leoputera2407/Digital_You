import { PlugIcon, SlackIcon, WorkspaceIcon } from "@/components/ui/icon"
import OrganizationSelect from "@/components/ui/orgSelector"
import { SidebarNav } from "@/components/ui/sidebar-nav"

const sidebarNavItems = [
  {
    title: "Work Space",
    href: "/settings/admin/workspace",
    icon: <WorkspaceIcon />,
  },
  {
    title: "Connectors",
    href: "/settings/admin/connectors",
    icon: <PlugIcon /> ,
  },
  {
    title: "Slack Integration",
    href: "/settings",
    icon: <SlackIcon />,
  },
]

interface SettingsLayoutProps {
  children: React.ReactNode
}

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  return (
    <>
      <div className="hidden space-y-6 p-10 pb-16 md:flex md:flex-col md:justify-center md:items-center md:space-y-8 mt-2">
        <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0 w-full lg:max-w-7xl overflow-hidden">
          <aside className="dark:bg-gray-900 pt-6 pb-6 lg:w-60 space-y-4">
            <OrganizationSelect />
            <SidebarNav items={sidebarNavItems} />
          </aside>
          <div className="flex-1 pt-6 pb-6">{children}</div>
        </div>
      </div>
    </>
  )
}
