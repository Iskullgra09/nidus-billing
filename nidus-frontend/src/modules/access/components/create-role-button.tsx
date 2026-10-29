"use client";

import * as React from "react";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/shared/ui/button";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { ScopeResponse } from "../types/scopes-catalog";
import { RoleFormDialog } from "./role-form-dialog";

interface CreateRoleButtonProps {
  scopes: ScopeResponse[];
}

export function CreateRoleButton({ scopes }: CreateRoleButtonProps) {
  const t = useTranslations("SettingsRoles");
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <CanAccess scope={NidusScope.ROLE_WRITE}>
        <Button size="sm" onClick={() => setOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("createRoleButton")}
        </Button>
      </CanAccess>
      <RoleFormDialog
        isOpen={open}
        onClose={setOpen}
        scopes={scopes}
        role={null}
      />
    </>
  );
}
