import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { IFormGroup } from '@rxweb/types';
import { Observable } from 'rxjs';
import { TranslationInternal, TranslationValue } from '../homescreen';

@Component({
  selector: 'rcc-home-screen-translations-editor',
  templateUrl: './home-screen-translations-editor.component.html',
  styleUrls: ['./home-screen-translations-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenTranslationsEditorComponent {
  @Input() translations: TranslationInternal[];
  @Input() formGroup: IFormGroup<TranslationValue>;
  @Output() removeTranslation = new EventEmitter<TranslationInternal>();

  translations$: Observable<string[]>;

  trackTranslation(index: number, item: TranslationInternal) {
    return item.key;
  }
}
