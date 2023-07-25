"use client";
import useAccount from "@/lib/hooks/useAccount";
import { OrganizationAssociationBase } from "@/lib/types";
import { ReactNode, createContext, useContext, useEffect, useState } from "react";

type OrganizationContextProps = {
  organizations: OrganizationAssociationBase[] | undefined;
  currentOrganization: OrganizationAssociationBase | null;
  switchOrganization: (organizationId: string) => void;
  isLoading: boolean;
  isError: boolean;
  revalidate: () => void;
};

const OrganizationContext = createContext<OrganizationContextProps | undefined>(
  undefined
);

type OrganizationProviderProps = {
  children: ReactNode;
};

export const OrganizationProvider = ({
  children,
}: OrganizationProviderProps) => {
  const { organizations, isLoading, isError, revalidate } = useAccount();

  // If organizations is not None, we sort the organizations by joined_at date
  // with the latest joined_at date first
  // This will only be set during the inital render and when switchOrganization is called
  let sortedOrganizations: OrganizationAssociationBase[] | null = null;
  if (organizations) {
    sortedOrganizations = [...organizations].sort((a, b) => new Date(a.joined_at).getTime() - new Date(b.joined_at).getTime());
  }
  const [currentOrganization, setCurrentOrganization] = useState<OrganizationAssociationBase | null>(null);

  useEffect(() => {
    // Try to get the saved organization ID from localStorage
    const savedOrganizationId = window.localStorage.getItem('selectedOrganization');
  
    if (savedOrganizationId) {
      // If there's a saved organization ID, find the corresponding organization
      const savedOrganization = organizations?.find((org) => org.id === savedOrganizationId);
      setCurrentOrganization(savedOrganization || null);
    } else if (sortedOrganizations && sortedOrganizations.length > 0) {
      // If there's no saved organization ID and sortedOrganizations is defined, use the first organization
      setCurrentOrganization(sortedOrganizations[0]);
    }
  }, [sortedOrganizations]);

  const switchOrganization = (organizationId: string) => {
    const newOrganization = organizations?.find(
      (org) => org.id === organizationId
    );
    setCurrentOrganization(newOrganization || null);
  };

  return (
    <OrganizationContext.Provider
      value={{
        organizations,
        currentOrganization,
        switchOrganization,
        isLoading,
        isError,
        revalidate,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
};

export const useOrganization = (): OrganizationContextProps => {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error(
      "useOrganization must be used within an OrganizationProvider"
    );
  }
  return context;
};
