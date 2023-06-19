"use client"

import { SliderProps } from "@radix-ui/react-slider"

import { FormField } from "@/components/react-hook-form/form"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/Hover-card"
import { Label } from "@/components/ui/Label"
import { Slider } from "@/components/ui/Slider"
import { UseFormReturn } from "react-hook-form"
import { ModelsFormValues } from "../data/type"


interface TemperatureSelectorProps extends SliderProps {
    form: UseFormReturn<ModelsFormValues>
}

export function TemperatureSelector({
  form,
  ...props
}: TemperatureSelectorProps) {

  return (
    <div className="grid gap-2 pt-2">
      <HoverCard openDelay={200}>
        <HoverCardTrigger asChild>
          < FormField
            control={form.control}
            name="temperature"
            render={({ field }) => (
              <div className="grid gap-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="temperature">Temperature</Label>
                  <span className="w-12 rounded-md border border-transparent px-2 py-0.5 text-right text-sm text-muted-foreground hover:border-border">
                    {field.value}
                  </span>
                </div>
                <Slider
                  id="temperature"
                  max={1}
                  defaultValue={[field.value]}
                  step={0.1}
                  onValueChange={value => field.onChange(value)}
                  className="[&_[role=slider]]:h-4 [&_[role=slider]]:w-4"
                  aria-label="Temperature"
                  {...props}
                />
              </div>
            )}
          />
        </HoverCardTrigger>
        <HoverCardContent
          align="start"
          className="w-[260px] text-sm"
          side="left"
        >
          Controls randomness: lowering results in less random completions. As
          the temperature approaches zero, the model will become deterministic
          and repetitive.
        </HoverCardContent>
      </HoverCard>
    </div>
  )
}