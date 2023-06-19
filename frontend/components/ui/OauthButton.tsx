import { ButtonHTMLAttributes, FC, LegacyRef, ReactNode, forwardRef } from "react";

interface OauthButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  icon?: ReactNode; // Add this prop to accept an SVG
  onClickHandler?: () => void; // Add this prop to accept an onClick function
}

export const OauthButton: FC<OauthButtonProps> = forwardRef((props, ref) => {
  const { isLoading, children, icon, onClickHandler, ...buttonProps } = props;

  return (
    <button
      onClick={onClickHandler}
      className="btn text-slate-300 hover:text-white transition duration-150 ease-in-out w-full group [background:linear-gradient(theme(colors.slate.900),_theme(colors.slate.900))_padding-box,_conic-gradient(theme(colors.slate.400),_theme(colors.slate.700)_25%,_theme(colors.slate.700)_75%,_theme(colors.slate.400)_100%)_border-box] relative before:absolute before:inset-0 before:bg-slate-800/30 before:rounded-full before:pointer-events-none h-9"
      disabled={isLoading}
      ref={ref as LegacyRef<HTMLButtonElement>}
      {...buttonProps}
    >
      <span className="relative">
        {icon} 
        {children}
      </span>
    </button>
  );
});

OauthButton.displayName = "OauthLoginButton";