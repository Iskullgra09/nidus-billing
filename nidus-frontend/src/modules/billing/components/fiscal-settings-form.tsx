"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { useRouter } from "@/core/i18n/routing";

import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { PasswordInput } from "@/shared/ui/password-input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { ConfirmDialog } from "@/shared/components/layout/confirm-dialog";
import {
  deleteHaciendaCredentialsAction,
  upsertFiscalProfileAction,
  upsertHaciendaCredentialsAction,
} from "../actions/fiscal";
import {
  FiscalProfile,
  HaciendaCredentialStatus,
  HaciendaEnvironment,
  IdentificationType,
} from "../types/fiscal";
import {
  CR_CANTONS,
  CR_DISTRICTS,
  CR_PROVINCES,
  crDistrictKey,
} from "../lib/cr-ubicacion";

interface FiscalSettingsFormProps {
  profile: FiscalProfile | null;
  credentials: HaciendaCredentialStatus | null;
}

const ID_TYPES: IdentificationType[] = [
  "fisica",
  "juridica",
  "dimex",
  "nite",
  "extranjero",
];

export function FiscalSettingsForm({
  profile,
  credentials,
}: FiscalSettingsFormProps) {
  const t = useTranslations("SettingsFiscal");
  const router = useRouter();
  const [savingProfile, setSavingProfile] = React.useState(false);
  const [savingCreds, setSavingCreds] = React.useState(false);
  const [confirmClear, setConfirmClear] = React.useState(false);

  const [legalName, setLegalName] = React.useState(profile?.legal_name ?? "");
  const [tradeName, setTradeName] = React.useState(profile?.trade_name ?? "");
  const [idType, setIdType] = React.useState<IdentificationType>(
    profile?.identification_type ?? "juridica",
  );
  const [idNumber, setIdNumber] = React.useState(
    profile?.identification_number ?? "",
  );
  const [activity, setActivity] = React.useState(
    profile?.economic_activity_code ?? "",
  );
  const [branch, setBranch] = React.useState(profile?.branch_code ?? "");
  const [province, setProvince] = React.useState(profile?.province ?? "");
  const [canton, setCanton] = React.useState(profile?.canton ?? "");
  const [district, setDistrict] = React.useState(profile?.district ?? "");
  const [otherSigns, setOtherSigns] = React.useState(profile?.other_signs ?? "");
  const [phone, setPhone] = React.useState(profile?.phone ?? "");
  const [email, setEmail] = React.useState(profile?.email ?? "");

  const [environment, setEnvironment] = React.useState<HaciendaEnvironment>(
    credentials?.environment ?? "sandbox",
  );
  const [username, setUsername] = React.useState(credentials?.username ?? "");
  const [p12Password, setP12Password] = React.useState("");
  const [pin, setPin] = React.useState("");
  const [oauthClientId, setOauthClientId] = React.useState(
    credentials?.oauth_client_id ?? "",
  );
  const [oauthSecret, setOauthSecret] = React.useState("");
  const [p12File, setP12File] = React.useState<File | null>(null);

  const cantonOptions = CR_CANTONS[province] ?? [];
  const districtOptions = CR_DISTRICTS[crDistrictKey(province, canton)] ?? [];
  const legalNameLabel =
    idType === "juridica" ? t("legalNameCompany") : t("legalNamePerson");

  const onProvinceChange = (value: string) => {
    setProvince(value);
    setCanton("");
    setDistrict("");
  };

  const onCantonChange = (value: string) => {
    setCanton(value);
    setDistrict("");
  };

  const saveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!legalName.trim() || !idNumber.trim()) {
      toast.error(t("profileRequired"));
      return;
    }
    setSavingProfile(true);
    const result = await upsertFiscalProfileAction({
      legal_name: legalName.trim(),
      trade_name: tradeName.trim() || null,
      identification_type: idType,
      identification_number: idNumber.trim(),
      economic_activity_code: activity.trim() || null,
      branch_code: branch.trim() || null,
      province: province.trim() || null,
      canton: canton.trim() || null,
      district: district.trim() || null,
      other_signs: otherSigns.trim() || null,
      phone: phone.trim() || null,
      email: email.trim() || null,
      country_code: "CR",
    });
    setSavingProfile(false);
    if (result.status === "success") {
      toast.success(result.message);
      router.refresh();
    } else toast.error(result.message);
  };

  const saveCredentials = async (event: React.FormEvent) => {
    event.preventDefault();
    setSavingCreds(true);
    const formData = new FormData();
    formData.set("environment", environment);
    if (username.trim()) formData.set("username", username.trim());
    if (p12Password) formData.set("p12_password", p12Password);
    if (pin) formData.set("pin", pin);
    if (oauthClientId.trim()) formData.set("oauth_client_id", oauthClientId.trim());
    if (oauthSecret) formData.set("oauth_client_secret", oauthSecret);
    if (p12File) formData.set("p12_file", p12File);
    const result = await upsertHaciendaCredentialsAction(formData);
    setSavingCreds(false);
    if (result.status === "success") {
      toast.success(result.message);
      setP12Password("");
      setPin("");
      setOauthSecret("");
      setP12File(null);
      router.refresh();
    } else toast.error(result.message);
  };

  const clearCredentials = async () => {
    const result = await deleteHaciendaCredentialsAction();
    setConfirmClear(false);
    if (result.status === "success") {
      toast.success(result.message);
      router.refresh();
    } else toast.error(result.message);
  };

  return (
    <div className="max-w-3xl space-y-10">
      <form onSubmit={(e) => void saveProfile(e)} className="space-y-4">
        <div>
          <h3 className="text-base font-semibold">{t("profileTitle")}</h3>
          <p className="text-sm text-muted-foreground">{t("profileDescription")}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="legal_name">{legalNameLabel}</Label>
            <Input
              id="legal_name"
              value={legalName}
              onChange={(e) => setLegalName(e.target.value)}
              required
            />
          </div>
          {idType === "juridica" ? (
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="trade_name">{t("tradeName")}</Label>
              <Input
                id="trade_name"
                value={tradeName}
                onChange={(e) => setTradeName(e.target.value)}
              />
            </div>
          ) : null}
          <div className="space-y-2">
            <Label>{t("identificationType")}</Label>
            <Select
              value={idType}
              onValueChange={(v) => setIdType(v as IdentificationType)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ID_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {t(`idTypes.${type}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="id_number">{t("identificationNumber")}</Label>
            <Input
              id="id_number"
              value={idNumber}
              onChange={(e) => setIdNumber(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="activity">{t("economicActivity")}</Label>
            <Input
              id="activity"
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
              placeholder={t("economicActivityPlaceholder")}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="branch">{t("branchCode")}</Label>
            <Input
              id="branch"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder={t("branchCodePlaceholder")}
            />
          </div>
          <div className="sm:col-span-2 pt-2">
            <h4 className="text-sm font-medium">{t("domicileTitle")}</h4>
          </div>
          <div className="space-y-2">
            <Label>{t("province")}</Label>
            <Select value={province || undefined} onValueChange={onProvinceChange}>
              <SelectTrigger>
                <SelectValue placeholder={t("selectLocation")} />
              </SelectTrigger>
              <SelectContent>
                {CR_PROVINCES.map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("canton")}</Label>
            <Select
              value={canton || undefined}
              onValueChange={onCantonChange}
              disabled={!province}
            >
              <SelectTrigger>
                <SelectValue placeholder={t("selectLocation")} />
              </SelectTrigger>
              <SelectContent>
                {cantonOptions.map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("district")}</Label>
            <Select
              value={district || undefined}
              onValueChange={setDistrict}
              disabled={!canton}
            >
              <SelectTrigger>
                <SelectValue placeholder={t("selectLocation")} />
              </SelectTrigger>
              <SelectContent>
                {districtOptions.map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">{t("phone")}</Label>
            <Input
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="other_signs">{t("otherSigns")}</Label>
            <Input
              id="other_signs"
              value={otherSigns}
              onChange={(e) => setOtherSigns(e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="email">{t("email")}</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>
        <Button type="submit" disabled={savingProfile}>
          {savingProfile ? t("saving") : t("saveProfile")}
        </Button>
      </form>

      <form
        onSubmit={(e) => void saveCredentials(e)}
        className="space-y-4 border-t border-border/70 pt-8"
      >
        <div>
          <h3 className="text-base font-semibold">{t("credentialsTitle")}</h3>
          <p className="text-sm text-muted-foreground">
            {t("credentialsDescription")}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            {credentials?.configured
              ? t("credentialsConfigured", {
                  environment: credentials.environment,
                })
              : t("credentialsEmpty")}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>{t("environment")}</Label>
            <Select
              value={environment}
              onValueChange={(v) => setEnvironment(v as HaciendaEnvironment)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sandbox">{t("envSandbox")}</SelectItem>
                <SelectItem value="production">{t("envProduction")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="mh_user">{t("username")}</Label>
            <Input
              id="mh_user"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="p12">{t("p12File")}</Label>
            <Input
              id="p12"
              type="file"
              accept=".p12,.pfx"
              onChange={(e) => setP12File(e.target.files?.[0] ?? null)}
            />
            {credentials?.has_p12 ? (
              <p className="text-xs text-muted-foreground">{t("p12Present")}</p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="p12_pass">{t("p12Password")}</Label>
            <PasswordInput
              id="p12_pass"
              value={p12Password}
              onChange={(e) => setP12Password(e.target.value)}
              autoComplete="new-password"
              placeholder={
                credentials?.has_p12 ? t("secretLeaveBlank") : undefined
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="pin">{t("pin")}</Label>
            <PasswordInput
              id="pin"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              autoComplete="new-password"
              placeholder={
                credentials?.configured ? t("secretLeaveBlank") : undefined
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="oauth_id">{t("oauthClientId")}</Label>
            <Input
              id="oauth_id"
              value={oauthClientId}
              onChange={(e) => setOauthClientId(e.target.value)}
              autoComplete="off"
              placeholder="api-stag"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="oauth_secret">{t("oauthClientSecret")}</Label>
            <PasswordInput
              id="oauth_secret"
              value={oauthSecret}
              onChange={(e) => setOauthSecret(e.target.value)}
              autoComplete="new-password"
              placeholder={
                credentials?.configured ? t("secretLeaveBlank") : undefined
              }
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={savingCreds}>
            {savingCreds ? t("saving") : t("saveCredentials")}
          </Button>
          {credentials?.configured ? (
            <Button
              type="button"
              variant="destructive"
              onClick={() => setConfirmClear(true)}
            >
              {t("clearCredentials")}
            </Button>
          ) : null}
        </div>
      </form>

      <ConfirmDialog
        open={confirmClear}
        onOpenChange={setConfirmClear}
        title={t("clearDialogTitle")}
        description={t("clearDialogDescription")}
        confirmLabel={t("clearCredentials")}
        variant="destructive"
        onConfirm={clearCredentials}
      />
    </div>
  );
}
