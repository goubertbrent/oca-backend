import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { IonicSelectableComponent } from 'ionic-selectable';
import { Product, ProductDetails, SelectedProduct, SelectedProductsMapping } from '../../../appointments';

@Component({
  selector: 'app-jcc-create-appointment',
  templateUrl: './jcc-create-appointment.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class JccCreateAppointmentComponent implements OnChanges {
  @ViewChild(IonicSelectableComponent, {static: true}) selectableComponent: IonicSelectableComponent;
  @Input() products: Product[];
  @Input() selectedProducts: SelectedProduct[];
  @Input() productCounts: SelectedProductsMapping;
  @Output() productSelected = new EventEmitter<Product>();
  @Output() updateProduct = new EventEmitter<{ productId: string; amount: number; }>();
  @Output() deleteProduct = new EventEmitter<{ productId: string }>();
  @Output() infoClicked = new EventEmitter<ProductDetails>();
  selectableProductCounts: { [ key: string ]: number[] } = {};

  @Input() set productsLoading(value: boolean) {
    if (this.selectableComponent) {
      if (value) {
        this.selectableComponent.showLoading();
      } else {
        this.selectableComponent.hideLoading();
      }
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.products && this.products) {
      for (const product of this.products) {
        if (!(product.productId in this.selectableProductCounts)) {
          const arrayLength = (product.productMaxCountForEvent || 10);
          this.selectableProductCounts[ product.productId ] = Array.from(Array(arrayLength), (_, x) => x + 1);
        }
      }
    }
  }

  onProductSelected({ component, value }: { component: IonicSelectableComponent; value: Product }) {
    this.productSelected.emit(value);
    component.clear();
  }

  amountChanged(productId: string, amount: number) {
    this.updateProduct.emit({ productId, amount });
  }

  trackByValue(index: number, amount: number) {
    return amount;
  }

  trackSelectedProduct(index: number, product: SelectedProduct) {
    return product.id;
  }
}
