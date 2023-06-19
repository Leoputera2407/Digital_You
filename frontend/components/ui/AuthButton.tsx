import { ButtonHTMLAttributes, FC, LegacyRef, forwardRef } from "react";
import { FaSpinner } from "react-icons/fa";


export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    isLoading?: boolean;
}

const AuthButton: FC<ButtonProps> = forwardRef((
    { 
        className, 
        children, 
        isLoading = false, 
        ...props 
    },
      forwardedRef
) => {

  return (
    <button
      className={className} // You might need to modify how classnames are combined
      disabled={isLoading}
      {...props}
      ref={forwardedRef as LegacyRef<HTMLButtonElement>}
      >
      {children} {isLoading && <FaSpinner className="animate-spin" />}
    </button>
  );
});

AuthButton.displayName = "AuthButton";
export default AuthButton;