import { ChangeDetectionStrategy, Component } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { getLanguage } from '@oca/shared';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { getCirkloInfo } from '../../cirklo.selectors';

function translate(mapping: { [ key: string ]: string }): string {
  const lang = rogerthat.user.language;
  const resolvedLang = getLanguage(lang, Object.keys(mapping));
  return mapping[ resolvedLang ];
}

@Component({
  selector: 'cirklo-info-page',
  templateUrl: './info-page.component.html',
  styleUrls: ['./info-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InfoPageComponent {
  logoUrl$: Observable<string | undefined>;
  infoText$: Observable<string>;
  buttons$: Observable<{ url: string; label: string }[] | undefined>;

  constructor(private store: Store) {
    const info = this.store.pipe(select(getCirkloInfo));
    this.logoUrl$ = info.pipe(map(i => i?.logo));
    this.infoText$ = info.pipe(map(i => i?.title ? translate(i.title) : ''));
    this.buttons$ = info.pipe(map(i => i?.buttons?.map(b => ({ url: b.url, label: translate(b.labels) }))));
  }

}
