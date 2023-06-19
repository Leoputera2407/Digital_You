import { ToastContext } from "@/components/ui/Toast/domain/ToastContext";
import { useContext } from "react";

export const useToast = () => {
  const { publish } = useContext(ToastContext);

  return {
    publish,
  };
};