import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { HoplrImage, HoplrMessageImage } from '../../hoplr';
import { ImageViewerComponent } from '../image-viewer/image-viewer.component';

@Component({
  selector: 'hoplr-feed-images',
  templateUrl: './feed-images.component.html',
  styleUrls: ['./feed-images.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedImagesComponent {
  @Input() images: HoplrImage[] | HoplrMessageImage[];

  constructor(private modelController: ModalController) {
  }

  async showImagesModal(imageIndex: number) {
    const modal = await this.modelController.create({
      component: ImageViewerComponent,
      componentProps: { images: this.images, imageIndex },
    });
    return await modal.present();
  }
}
