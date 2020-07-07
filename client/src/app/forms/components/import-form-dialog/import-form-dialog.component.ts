import { ChangeDetectionStrategy, ChangeDetectorRef, Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { CreateDynamicForm } from '../../interfaces/forms';

@Component({
  selector: 'oca-import-form-dialog',
  templateUrl: './import-form-dialog.component.html',
  styleUrls: ['./import-form-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImportFormDialogComponent {
  error: string | null = null;

  constructor(private dialogRef: MatDialogRef<ImportFormDialogComponent>,
              private changeDetectorRef: ChangeDetectorRef,
              private translate: TranslateService) {
  }

  importForm(fileInput: HTMLInputElement) {
    const reader = new FileReader();
    if (fileInput.files && fileInput.files.length) {
      const file = fileInput.files[ 0 ];
      reader.readAsText(file);
      reader.onload = () => {
        try {
          const parsed: { version: number; form: CreateDynamicForm } = JSON.parse(reader.result as string);
          this.dialogRef.close(parsed.form);
        } catch (e) {
          console.error(e);
          this.error = this.translate.instant('oca.this_is_not_a_valid_form');
        }
        this.changeDetectorRef.markForCheck();
      };
    } else {
      this.error = this.translate.instant('oca.select_a_file');
    }
  }
}
