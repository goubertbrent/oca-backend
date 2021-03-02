import {Component, OnInit} from '@angular/core';
import {environment} from "../../../../environments/environment";
import {Store} from "@ngrx/store";
import {changeLayer, clickMarker} from "../../map.actions";

@Component({
  selector: 'app-layerbar',
  templateUrl: './layerbar.component.html',
  styleUrls: ['./layerbar.component.scss']
})
export class LayerbarComponent implements OnInit {

  PROFITKEY = environment.servicesProfitLayerId;
  NON_PROFITKEY = environment.servicesNonProfitLayerId;
  CAREKEY = environment.servicesCareLayerId;
  CITYKEY = environment.servicesCityLayerId;

  isProfitSelected = false;
  isNonProfitSelected = false;
  isCareSelected = false;
  isCitySelected = true;

  constructor(private store: Store) {
  }

  ngOnInit(): void {
  }

  selectLayer(layerId: string) {

    if (layerId == this.PROFITKEY) {
      this.isProfitSelected = true
      this.isNonProfitSelected = false
      this.isCareSelected = false
      this.isCitySelected = false
    } else if (layerId == this.NON_PROFITKEY) {
      this.isNonProfitSelected = true
      this.isProfitSelected= false
      this.isCareSelected = false
      this.isCitySelected = false
    } else if (layerId == this.CITYKEY) {
      this.isCitySelected = true
      this.isNonProfitSelected = false
      this.isCareSelected = false
      this.isProfitSelected = false
    } else {
      this.isCareSelected = true
      this.isNonProfitSelected = false
      this.isProfitSelected = false
      this.isCitySelected = false
    }

    this.store.dispatch(changeLayer({layerId: layerId}));
  }
}
