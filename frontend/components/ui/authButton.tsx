import { ButtonHTMLAttributes, FC, LegacyRef, forwardRef } from "react";
import { FaSpinner } from "react-icons/fa";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

const AuthButton: FC<ButtonProps> = forwardRef(
  (
    { className, children, isLoading = false, ...props },
    forwardedRef
  ) => {
    return (
      <button
        className={`flex items-center justify-center relative ${className}`}
        disabled={isLoading}
        {...props}
        ref={forwardedRef as LegacyRef<HTMLButtonElement>}
      >
        <span className={`transition-all duration-200 ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
          {children}
        </span>
        {isLoading && (
          <span className="absolute top-0 left-0 flex items-center justify-center h-full w-full">
            <FaSpinner className="h-5 w-5 text-white animate-spin" />
          </span>
        )}
      </button>
    );
  }
);

AuthButton.displayName = "AuthButton";
export default AuthButton;