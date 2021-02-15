import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { IFormGroup } from '@rxweb/types';
import { NewsGroup } from '../../news/news';
import { TranslationInternal, TranslationValue } from '../homescreen';
import { HomeScreenBottomSheet, HomeScreenBottomSheetHeader } from '../models';

@Component({
  selector: 'rcc-home-screen-bottom-sheet',
  templateUrl: './home-screen-bottom-sheet.component.html',
  styleUrls: ['./home-screen-bottom-sheet.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenBottomSheetComponent {
  @Input() newsGroups: NewsGroup[];
  @Input() formGroup: IFormGroup<HomeScreenBottomSheet>;
  @Input() translations: TranslationInternal[];
  @Input() translationsMapping: TranslationValue = {};
  @Output() addTranslation = new EventEmitter();

  get headerControls() {
    return (this.formGroup.controls.header as IFormGroup<HomeScreenBottomSheetHeader>).controls;
  }

}
