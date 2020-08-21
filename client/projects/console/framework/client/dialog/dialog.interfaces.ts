export interface AlertDialogData {
  title?: string;
  message: string;
  ok: string;
}

export interface ConfirmDialogData extends AlertDialogData {
  cancel: string;
}

export interface PromptDialogData extends ConfirmDialogData {
  initialValue?: string;
  required?: boolean;
  inputType?: string;
}

export interface PromptDialogResult {
  submitted: boolean;
  value: string;
}
