"use client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
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
      <SelectTrigger className="w-full flex justify-between items-center">
        <span className="text-gray-500 mr-2">Organization: </span>
        <SelectValue 
         placeholder="Select an organization" 
         className="font-bold overflow-hidden overflow-ellipsis whitespace-nowrap flex-1 text-right"
        />
      </SelectTrigger>
      <SelectContent className="relative z-10  bg-white">
        {organizations && organizations.map(org => (
          <SelectItem key={org.id} value={org.id}  className="text-gray-900">
            {org.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default OrganizationSelect;
