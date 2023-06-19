"use client";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { useSupabase } from '@/lib/auth/authProvider';
import { useAxios } from '@/lib/hooks/useAxios';
import { useToast } from '@/lib/hooks/useToast';
import { getModelAPIKey, upsertModelAPIKey, validateModelAPIKey } from "@/lib/llm";
import { APIKeyJson, APIKeyType, ModelAPIKeyTypesArray } from "@/lib/types";
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';


interface ApiKeyRowProps {
  keyType: APIKeyType;
  apiKey: APIKeyJson | null;
}

interface FormValues {
  apiKeyValue: string;
}

function ApiKeyRow({ keyType, apiKey }: ApiKeyRowProps) {
  const { publish } = useToast();
  const { axiosInstance } = useAxios();
  const { user } = useSupabase();
  const [testingText, setTestingText] = useState<string | null>(null);
  const [buttonState, setButtonState] = useState<'testing' | 'upsert'>('testing');
  const [keyValue, setKeyValue] = useState(apiKey?.key_value || "");

  const { register, handleSubmit } = useForm<FormValues>();

  const onSubmitTest = (data: { apiKeyValue: string }) => {
    const apiKeyToTest: APIKeyJson = {
      key_type: keyType,
      key_value: data.apiKeyValue
    };
  
    validateModelAPIKey(axiosInstance, apiKeyToTest)
      .then(() => {
        setButtonState('upsert');
        setTestingText(`Successfully tested ${keyType}!`);
      })
      .catch((error: any) => {
        console.error("Error:", error);
        setTestingText(`Error: either your ${keyType} is invalid or you're out of quota!`);
      });
  };
  
  
  const onSubmitUpsert = (data: { apiKeyValue: string }) => {
    if (user?.id) {
      const newAPIKey: APIKeyJson = { 
        key_type: keyType,
        key_value: data.apiKeyValue
      };      
      upsertModelAPIKey(axiosInstance, user.id, newAPIKey)
        .then(() => {
          // When the operation is successful, show a toast
          publish({
            variant: "success",
            text: `Successfully ${apiKey ? 'updated' : 'set up'} ${keyType} API Key!`
          });
        })
        .catch((error: any) => {
          console.error("Error:", error);
          // You can also add a toast for the error case if you want
          publish({
            variant: "danger",
            text: `Failed to ${apiKey ? 'update' : 'set up'} ${keyType} API Key. Please try again!`
          });
        });
    }
  };

  return (
    <div className="flex justify-between items-center mb-4">
      <h2 className="text-lg">{keyType}</h2>
      <Badge>{apiKey ? 'Enabled' : 'Disabled'}</Badge>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="outline">{apiKey ? 'Update' : 'Setup'}</Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[425px]">
          <form onSubmit={handleSubmit(buttonState === 'testing' ? onSubmitTest : onSubmitUpsert)}>
            <DialogHeader>
              <DialogTitle>{apiKey ? 'Update' : 'Setup'} {keyType}</DialogTitle>
              <DialogDescription>
                Enter the API key for {keyType} here.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor={keyType} className="text-right">
                  API Key
                </Label>
                <Input id={keyType} {...register("apiKeyValue")} defaultValue={keyValue} className="col-span-3" />
                {testingText && <div className={buttonState === 'testing' ? 'text-red-500' : 'text-green-500'}>{testingText}</div>}

              </div>
            </div>
            <DialogFooter>
              <Button type="submit">
                {buttonState === 'testing' ? 'Test' : 'Enable'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}


export function ModelProviderForm() {
  const { session, user } = useSupabase();
  const { axiosInstance } = useAxios();
  const [apiKeys, setApiKeys] = useState({});

  useEffect(() => {
   console.log("session", session)
    getModelAPIKey(axiosInstance, user?.id)
      .then((apiKeys: APIKeyJson[]) => {
        const keys: Partial<Record<APIKeyType, APIKeyJson>> = {};
        apiKeys.forEach(key => {
          keys[key.key_type] = key;
        });
        setApiKeys(keys);
      })
      .catch((error) => console.error("Error:", error));
    
  }, [axiosInstance, user, session]);

  return (
    <div className="space-y-4">
      {ModelAPIKeyTypesArray.map((keyType) => (
        <ApiKeyRow key={keyType} keyType={keyType} apiKey={apiKeys[keyType]} />
      ))}
    </div>
  );
}