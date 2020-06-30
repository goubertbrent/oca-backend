import { ChangeDetectionStrategy, Component, Input, OnInit, ViewChild } from '@angular/core';
import { IonSlides, ModalController } from '@ionic/angular';
import { HoplrImage, HoplrMessageImage } from '../../hoplr';

@Component({
  selector: 'hoplr-image-viewer',
  templateUrl: './image-viewer.component.html',
  styleUrls: ['./image-viewer.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImageViewerComponent implements OnInit{
  options = {
    autoHeight: true,
  };
  @ViewChild(IonSlides, { static: true }) slides: IonSlides;

  @Input() images: HoplrImage[] | HoplrMessageImage[];

  @Input() set imageIndex(value: number) {
    this.slides.getSwiper().then(s => {
      s.slideTo(value);
    });
  }

  constructor(private modal: ModalController) {
  }

  ngOnInit() {
    // Fix issue with slides where they become all buggy after opening this dialog twice
    // See https://github.com/ionic-team/ionic/issues/19638
    this.slides.update();
  }

  closeModal() {
    this.modal.dismiss();
  }
}
