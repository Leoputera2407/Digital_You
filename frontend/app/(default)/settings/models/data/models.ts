import { SupportedModels } from "@/lib/types";


export interface Model<SupportedModels = string> {
  id: string
  name: string
  description: string
  type: SupportedModels
}

// TODO: For now hard-code, I think it makes sense to put this in the DB. Also, we should try to make it consistent
// with the types names in the backend i.e the stuff at @/lib/types.
export const models: Model<SupportedModels>[] = [
  {
    id: "1",
    name: "gpt-3.5-turbo",
    description:
      "The fastest GPT model.",
    type: "GPT3_5",
  },
  {
    id: "2",
    name: "gpt-4",
    description: 
        "The most capable GPT model, but very expensive.",
    type: "GPT4",
  },
  {
    id: "3",
    name: "claude",
    description: 
        "Capable, and can support really long context -- 100k tokens.",
    type: "ANTROPHIC",
  },
]