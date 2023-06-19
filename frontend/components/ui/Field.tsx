import { cn } from "@/lib/utils";
import {
    DetailedHTMLProps,
    InputHTMLAttributes,
    RefObject,
    forwardRef,
} from "react";

interface FieldProps
  extends DetailedHTMLProps<
    InputHTMLAttributes<HTMLInputElement>,
    HTMLInputElement
  > {
  label?: string;
  name: string;
}

const Field = forwardRef(
  ({ label, className, name, ...props }: FieldProps, forwardedRef) => {
    return (
      <div className={cn("block w-full", className)} name={name}>
        {label && (
          <label
            htmlFor={name}
            className="text-sm text-slate-300 font-medium mb-1"
          >
            {label}
          </label>
        )}
        <input
          ref={forwardedRef as RefObject<HTMLInputElement>}
          className="form-input w-full"
          name={name}
          id={name}
          {...props}
        />
      </div>
    );
  }
);
Field.displayName = "Field";

export default Field;