import { OauthButton } from "@/components/ui/OauthButton";
import { useGithubLogin } from "./hooks/useGithubLogin";

export const GithubLoginButton = () => {
  const { isPending, signInWithGithub } = useGithubLogin();

  const googleIcon = (
    <svg
      className="fill-current"
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="15"
    >
        <path d="M7.488 0C3.37 0 0 3.37 0 7.488c0 3.276 2.153 6.084 5.148 7.113.374.094.468-.187.468-.374v-1.31c-2.06.467-2.527-.936-2.527-.936-.375-.843-.843-1.124-.843-1.124-.655-.468.094-.468.094-.468.749.094 1.123.75 1.123.75.655 1.216 1.778.842 2.153.654.093-.468.28-.842.468-1.03-1.685-.186-3.37-.842-3.37-3.743 0-.843.281-1.498.75-1.966-.094-.187-.375-.936.093-1.965 0 0 .655-.187 2.059.749a6.035 6.035 0 0 1 1.872-.281c.655 0 1.31.093 1.872.28 1.404-.935 2.059-.748 2.059-.748.374 1.03.187 1.778.094 1.965.468.562.748 1.217.748 1.966 0 2.901-1.778 3.463-3.463 3.65.281.375.562.843.562 1.498v2.059c0 .187.093.468.561.374 2.996-1.03 5.148-3.837 5.148-7.113C14.976 3.37 11.606 0 7.488 0Z" />
    </svg>
  );

  return (
    <>
      <OauthButton
        onClickHandler={signInWithGithub}
        isLoading={isPending}
        icon={googleIcon}
      >
        <span className="sr-only">Continue with Github</span>
      </OauthButton>
    </>
  );
};
