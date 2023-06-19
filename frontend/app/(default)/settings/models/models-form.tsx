"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Form } from "@/components/react-hook-form/form";
import { Button } from "@/components/ui/Button";
import { useSupabase } from "@/lib/auth/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { getModelConfig, upsertModelConfig } from "@/lib/llm";
import { SupportedModelsArray } from "@/lib/types";
import { redirect } from "next/navigation";
import { ModelSelector } from "./components/model-selector";
import { TemperatureSelector } from "./components/temperature-selector";
import { models } from "./data/models";
import { ModelsFormSchema, ModelsFormValues } from "./data/type";

export function ModelsForm() {
  const { publish } = useToast();
  const [defaultValues, setDefaultValues] = useState<Partial<ModelsFormValues>>(
    {}
  );
  const { user, session } = useSupabase();

  if (session?.user !== undefined) {
    redirect("/signin");
  }

  useEffect(() => {
    if (user?.id) {
      getModelConfig(user?.id)
        .then((data) => setDefaultValues(data))
        .catch((error) => console.error("Error:", error));
    } else {
      publish({
        variant: "danger",
        text: `You need to be logged in to use this feature!`,
      });
    }
  }, [user]);

  const form = useForm<ModelsFormValues>({
    resolver: zodResolver(ModelsFormSchema),
    defaultValues,
  });

  async function onSubmit(data: ModelsFormValues) {
    try {
      if (user?.id) {
        // This function call might throw an exception
        await upsertModelConfig(user.id, {
          supported_model_enum: data.model_type,
          temperature: data.temperature,
        });
        publish({
          variant: "success",
          text: `You're using ${data.model_type} with temperature ${data.temperature}!`,
        });
      } 
    } catch (error) {
      console.error("Error:", error);
      publish({
        variant: "danger",
        text: `Error updating model config: ${error.message}`,
      });
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <ModelSelector models={models} types={SupportedModelsArray} form={form} />
        <TemperatureSelector form={form} />
        `<Button type="submit">Update Model Config</Button>
      </form>
    </Form>
  );
}
