import { Separator } from "@/components/ui/Separator"
import { ModelProviderForm } from "./model-provider-form"

export default function SettingsProfilePage() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Model Providers</h3>
        <p className="text-sm text-muted-foreground">
          Model providers available to your apps.
        </p>
      </div>
      <Separator />
      <ModelProviderForm />
    </div>
  )
}
