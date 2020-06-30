import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { HoplrRsvp, HoplrRsvpType } from '../../hoplr';

interface RsvpList {
  label: string;
  items: HoplrRsvp[];
}

@Component({
  selector: 'hoplr-rsvp-list-modal',
  templateUrl: './rsvp-list-modal.component.html',
  styleUrls: ['./rsvp-list-modal.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RsvpListModalComponent {
  lists: RsvpList[] = [];

  constructor(private modal: ModalController) {
  }

  @Input() set rsvps(value: HoplrRsvp[]) {
    const mapping: { [key in HoplrRsvpType]: RsvpList } = {
      [ HoplrRsvpType.GOING ]: {
        label: 'app.hoplr.going',
        items: [],
      },
      [ HoplrRsvpType.INTERESTED ]: {
        label: 'app.hoplr.interested',
        items: [],
      },
    };
    for (const item of value) {
      mapping[ item.RsvpType ].items.push(item);
    }
    this.lists = Object.values(mapping).filter(v => v.items.length > 0);
  }

  closeModal() {
    this.modal.dismiss();
  }
}
