"use client"

import { PopoverProps } from "@radix-ui/react-popover"
import { Check, ChevronsUpDown } from "lucide-react"
import * as React from "react"

import { Button } from "@/components/ui/Button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/Command"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/Hover-card"
import { Label } from "@/components/ui/Label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/Popover"
import { useMutationObserver } from "@/lib/hooks/use-mutation-observer"
import { cn } from "@/lib/utils"

import { FormField } from "@/components/react-hook-form/form"
import { SupportedModels } from "@/lib/types"
import { UseFormReturn } from "react-hook-form"
import { Model } from "../data/models"
import { ModelsFormValues } from "../data/type"

interface ModelSelectorProps extends PopoverProps {
  types: readonly SupportedModels[]
  models: Model[]
  form: UseFormReturn<ModelsFormValues>
}

export function ModelSelector(
    { models, types, form, ...props }: ModelSelectorProps) {
  const [peekedModel, setPeekedModel] = React.useState<Model>(models[0])

  return (
    <div className="grid gap-2">
      <HoverCard openDelay={200}>
        <HoverCardTrigger asChild>
          <Label htmlFor="model">Model</Label>
        </HoverCardTrigger>
        <HoverCardContent
          align="start"
          className="w-[260px] text-sm"
          side="left"
        >
          The model which we'll call to perform QA and generate responses
        </HoverCardContent>
      </HoverCard>
      < FormField
        control={form.control}
        name="model_type"
        render={({ field }) => (
          <Popover open={field.value.type} onOpenChange={value => form.setValue("model_type", value)} {...props}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={field.value}
                aria-label="Select a model"
                className="w-full justify-between"
              >
                {field.value ? field.value.name : "Select a model..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-[250px] p-0">
              <HoverCard>
                <HoverCardContent
                  side="left"
                  align="start"
                  forceMount
                  className="min-h-[280px]"
                >
                  <div className="grid gap-2">
                    <h4 className="font-medium leading-none">{peekedModel.name}</h4>
                    <div className="text-sm text-muted-foreground">
                      {peekedModel.description}
                    </div>
                  </div>
                </HoverCardContent>
                <Command loop>
                  <CommandList className="h-[var(--cmdk-list-height)] max-h-[400px]">
                    <CommandInput placeholder="Search Models..." />
                    <CommandEmpty>No Models found.</CommandEmpty>
                    <HoverCardTrigger />
                    {types.map((type) => (
                      <CommandGroup key={type} heading={type}>
                        {models
                          .filter((model) => model.type === type)
                          .map((model) => (
                            <ModelItem
                              key={model.id}
                              model={model}
                              isSelected={field.value?.id === model.id}
                              onPeek={(model) => setPeekedModel(model)}
                              onSelect={() => {
                                form.setValue("model_type", model.type);
                                field.onChange(false); // To close the popover
                              }}
                            />
                          ))}
                      </CommandGroup>
                    ))}
                  </CommandList>
                </Command>
              </HoverCard>
            </PopoverContent>
          </Popover>
        )}
      />
    </div>
  );
}

interface ModelItemProps {
  model: Model
  isSelected: boolean
  onSelect: () => void
  onPeek: (model: Model) => void
}

function ModelItem({ model, isSelected, onSelect, onPeek }: ModelItemProps) {
  const ref = React.useRef<HTMLDivElement>(null)

  useMutationObserver(ref, (mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === "attributes") {
        if (mutation.attributeName === "aria-selected") {
          onPeek(model)
        }
      }
    }
  })

  return (
    <CommandItem
      key={model.id}
      onSelect={onSelect}
      ref={ref}
      className="aria-selected:bg-primary aria-selected:text-primary-foreground"
    >
      {model.name}
      <Check
        className={cn(
          "ml-auto h-4 w-4",
          isSelected ? "opacity-100" : "opacity-0"
        )}
      />
    </CommandItem>
  )
}