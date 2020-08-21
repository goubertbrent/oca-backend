export const MAX_BRANDING_SIZE = 1024 * 400;

export interface Branding {
  created_by_editor: boolean;
  description: string;
  id: string;
  timestamp: number;
  type: number;
}

export interface QrCodeTemplate {
  id?: number;
  key_name?: string;
  is_default: boolean;
  description: string;
  body_color: string;
  file?: string | null;
}

export interface DefaultBranding {
  id?: string;
  branding: string;
  app_ids: string[];
  branding_type: string;
  is_default: boolean;
}

export interface CreateDefaultBrandingPayload extends DefaultBranding {
  file: any;
}

export const DEFAULT_BRANDING_TYPES = [ {
  value: 'DefaultBirthdayMessageBranding',
  label: 'rcc.birthday_message',
  hint: 'rcc.birthday_message_hint',
} ];
