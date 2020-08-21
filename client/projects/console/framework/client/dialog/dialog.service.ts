import { ComponentType } from '@angular/cdk/portal';
import { Injectable, TemplateRef } from '@angular/core';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';
import { AlertDialogComponent, ConfirmDialogComponent, PromptDialogComponent } from './components';
import { AlertDialogData, ConfirmDialogData, PromptDialogData } from './dialog.interfaces';

@Injectable({providedIn: 'root'})
export class DialogService {
  constructor(public matDialog: MatDialog) {
  }

  open<T>(componentOrTemplateRef: ComponentType<T> | TemplateRef<T>, config?: MatDialogConfig): MatDialogRef<T> {
    return this.matDialog.open(componentOrTemplateRef, config);
  }

  openAlert(config: AlertDialogData): MatDialogRef<AlertDialogComponent> {
    return this.matDialog.open(AlertDialogComponent, { data: config });
  }

  openConfirm(config: ConfirmDialogData): MatDialogRef<ConfirmDialogComponent, boolean> {
    return this.matDialog.open(ConfirmDialogComponent, { data: config });
  }

  openPrompt(config: PromptDialogData): MatDialogRef<PromptDialogComponent, { submitted: boolean; value: string | null; }> {
    return this.matDialog.open(PromptDialogComponent, { data: config });
  }
}
