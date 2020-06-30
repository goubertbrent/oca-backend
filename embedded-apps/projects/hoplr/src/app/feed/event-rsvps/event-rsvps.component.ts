import { ChangeDetectionStrategy, Component, HostListener, Input } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { HoplrRsvp, HoplrRsvpType } from '../../hoplr';
import { RsvpListModalComponent } from '../rsvp-list-modal/rsvp-list-modal.component';

@Component({
  selector: 'hoplr-event-rsvps',
  templateUrl: './event-rsvps.component.html',
  styleUrls: ['./event-rsvps.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventRsvpsComponent {
  summary = '';

  constructor(private translate: TranslateService,
              private modalController: ModalController) {
  }

  private _rsvps: HoplrRsvp[] = [];

  get rsvps() {
    return this._rsvps;
  }

  @Input() set rsvps(value: HoplrRsvp[]) {
    this._rsvps = value;
    const parts = {
      [ HoplrRsvpType.GOING ]: {
        amount: 0,
        label: 'app.hoplr.going',
      },
      [ HoplrRsvpType.INTERESTED ]: {
        amount: 0,
        label: 'app.hoplr.interested',
      },
    };
    for (const rsvp of value) {
      parts[ rsvp.RsvpType ].amount++;
    }
    this.summary = Object.values(parts)
      .filter(v => v.amount > 0)
      .map(v => `${v.amount} ${this.translate.instant(v.label)}`)
      .join('·');
  };

  @HostListener('click')
  async onClick() {
    const modal = await this.modalController.create({ component: RsvpListModalComponent, componentProps: { rsvps: this._rsvps } });
    await modal.present();
  }
}
