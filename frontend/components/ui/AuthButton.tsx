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
      {
        isLoading && 
        <FaSpinner 
          className={`animate-spin mr-2 transition-all duration-200 ${isLoading ? 'opacity-100 transform translate-x-0' : 'opacity-0 transform -translate-x-2'}`} 
        />
      } {children} 
    </button>
  );
});

AuthButton.displayName = "AuthButton";
export default AuthButton;