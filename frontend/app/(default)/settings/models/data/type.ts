import { SupportedModelsArray } from "@/lib/types";
import * as z from "zod";

export const ModelsFormSchema = z.object({
    model_type: z.enum(SupportedModelsArray, {
      required_error: "You need to select a model type.",
    }),
    temperature: z
      .number({
        required_error: "You need to select a temperature.",
      })
      .min(0)
      .max(1)
      .default(0.5),
  });
  
 export type ModelsFormValues = z.infer<typeof ModelsFormSchema>;