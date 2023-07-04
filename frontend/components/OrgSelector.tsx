"use client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/Select";
import { useOrganization } from "@/lib/context/orgProvider";
import React from 'react';

const OrganizationSelect: React.FC = () => {
  const { organizations, currentOrganization, switchOrganization } = useOrganization();

  const handleOrganizationChange = (value: string) => {
    switchOrganization(value);
  };
  const isDisabled = !organizations || organizations.length === 0;
  return (
    <Select 
      value={currentOrganization?.id || ""} 
      onValueChange={handleOrganizationChange}
      disabled={isDisabled}
    >
      <SelectTrigger className="w-[250px]">
        <span className="text-gray-500 mr-2">Organization: </span>
        <SelectValue placeholder="Select an organization" className="font-bold"/>
      </SelectTrigger>
      <SelectContent>
        {organizations && organizations.map(org => (
          <SelectItem key={org.id} value={org.id}>
            {org.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default OrganizationSelect;
