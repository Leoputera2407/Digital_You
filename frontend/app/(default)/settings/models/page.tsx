import { Separator } from "@/components/ui/separator"
import { ModelsForm } from "../models/models-form"

export default function SettingsNotificationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Model Configuration</h3>
        <p className="text-sm text-muted-foreground">
          Configure the model you want to perform QA and chat as Digital You.
        </p>
      </div>
      <Separator />
      <ModelsForm />
    </div>
  )
}