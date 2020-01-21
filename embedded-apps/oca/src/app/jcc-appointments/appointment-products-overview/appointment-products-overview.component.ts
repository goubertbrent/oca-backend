import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { ProductDetails, SelectedProduct } from '../appointments';

@Component({
  selector: 'app-appointment-products-overview',
  templateUrl: './appointment-products-overview.component.html',
  styleUrls: ['./appointment-products-overview.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppointmentProductsOverviewComponent {
  @Input() selectedProducts: SelectedProduct[];

  constructor(private alertController: AlertController,
              private translate: TranslateService) {
  }

  async showProductRequisites(productDetails: ProductDetails) {
    const alert = await this.alertController.create({
      header: productDetails.description,
      message: `${this.translate.instant('app.oca.what_do_you_need')}
${productDetails.requisites}`,
      buttons: [{
        text: this.translate.instant('app.oca.ok'),
        role: 'cancel',
      }],
    });
    await alert.present();
  }
}
