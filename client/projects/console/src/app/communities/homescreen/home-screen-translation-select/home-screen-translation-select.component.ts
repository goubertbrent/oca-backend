import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { FormControl } from '@angular/forms';
import { TranslationInternal } from '../homescreen';

@Component({
  selector: 'rcc-home-screen-translation-select',
  templateUrl: './home-screen-translation-select.component.html',
  styleUrls: ['./home-screen-translation-select.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenTranslationSelectComponent {
  @Input() translations: TranslationInternal[] = [];
  @Input() required = false;
  @Input() label: string;
  @Input() control: FormControl;
  @Output() addTranslation = new EventEmitter();

  addClicked(event: Event) {
    event.stopPropagation();
    this.addTranslation.emit();
  }
}
