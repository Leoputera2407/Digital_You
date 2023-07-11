"use client";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useSupabase } from "@/lib/context/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { useEffect, useState } from "react";

export default function SignedInUser() {
  const { user, supabase } = useSupabase();
  const [dropdownVisible, setDropdownVisible] = useState(false);
  const { publish } = useToast();

  const handleLogOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      publish({
        variant: "danger",
        text: error.message,
      });
    }
  };

  // Function to handle click outside of dropdown
  useEffect(() => {
    const handleClickOutside = (event: any) => {
      if (dropdownVisible && !event.target.closest(".dropdown")) {
        setDropdownVisible(false);
      }
    };

    window.addEventListener("click", handleClickOutside);
    return () => window.removeEventListener("click", handleClickOutside);
  }, [dropdownVisible]);

  const avatarLetter =
    user && user.email ? user.email.charAt(0).toUpperCase() : "";

  return (
    <div className="relative dropdown">
      <Avatar onClick={() => setDropdownVisible(!dropdownVisible)}>
        <AvatarFallback className="bg-purple-500 text-white">
          {avatarLetter}
        </AvatarFallback>
      </Avatar>

      {dropdownVisible && (
        <ul className="absolute right-0 py-1 mt-1 bg-white rounded-lg shadow-xl text-sm">
          <li>
            <button
              onClick={handleLogOut}
              className="block text-center px-4 py-1 text-gray-800 hover:bg-gray-500 hover:bg-opacity-20 whitespace-nowrap"
            >
              Log Out
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}
