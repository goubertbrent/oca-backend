/* tslint:disable:no-trailing-whitespace */
import {Component, OnInit} from '@angular/core';
import {select, Store} from '@ngrx/store';
import {clickMarker} from '../map.actions';

import * as  mapboxgl from 'mapbox-gl';
import {Marker, SelectedMarker} from "../marker.model";
import {environment} from "../../../environments/environment";
import {Observable} from "rxjs";
import {getLayerId} from "../map.selectors";

interface Source {
  sourceId: string;
  tileId: string;
  tileName: string;
}

@Component({
  selector: 'app-mapbox',
  templateUrl: './mapbox.component.html',
  styleUrls: ['./mapbox.component.scss']
})
export class MapboxComponent implements OnInit {
  private layers = [environment.servicesCityLayerId, environment.servicesProfitLayerId,
  environment.servicesNonProfitLayerId ,environment.servicesCareLayerId]
  selectedLayerId$: Observable<string>;

  private map: any;
  private selectedLayerId: string | null = null;

  constructor(private store: Store) {}

  public onClickMarker(feature: Marker) {
    let test: SelectedMarker = {
      'id': feature.id,
      'properties': JSON.parse(feature.properties.data),
      'type': feature.type,
      'geometry': feature.geometry,
    }
    this.store.dispatch(clickMarker({selectedMarker: test}));
  }

  ChangeLayer(layerId: string, visibility: string): void {
    if(this.selectedLayerId)
    {
     this.hideLayer(this.selectedLayerId)
    }
    this.selectedLayerId = layerId;

    this.map.setLayoutProperty(layerId, 'visibility', visibility);
  }

  ngOnInit(): void {
    this.map = new mapboxgl.Map({
      accessToken: 'pk.eyJ1IjoiZmFpcnZpbGxlIiwiYSI6ImNrbDZkb2ppNzFjeXQycW1uOGM0cDY1NmQifQ.-l4ZEOYtpkk39Re3txcSNw',
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [3.7174, 51.0543],
      maxZoom: 20,
      minZoom: 5,
      zoom: 10
    });

    const servicesCity = {
      sourceId: environment.servicesCityLayerId,
      tileId: 'fairville.services_city',
      tileName: 'services_city'
    };
    const servicesNonProfit = {
      sourceId: environment.servicesNonProfitLayerId, tileId: 'fairville.services_non_profit',
      tileName: 'services_non_profit'
    };
    const servicesProfit = {
      sourceId: environment.servicesProfitLayerId,
      tileId: 'fairville.services_profit',
      tileName: 'services_profit'
    };
    const servicesCare = {
      sourceId: environment.servicesCareLayerId,
      tileId: 'fairville.services_emergency',
      tileName: 'services_emergency'
    };

// Create a popup, but don't add it to the map yet.
    const popup = new mapboxgl.Popup({
      closeButton: false
    });

    this.map.on('load', () => {

      this.map.resize();

      this.addImage('../../../assets/images/icons/grocery_store.png', 'grocery_store');
      this.addImage('../../../assets/images/icons/location_city.png', 'location_city');
      this.addImage('../../../assets/images/icons/medical_services.png', 'medical_services');
      this.addImage('../../../assets/images/icons/sports_football.png', 'sports_football');
      this.addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=false&size=64&grey=false', 'workassignmentOrangeIcon');
      this.addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=true', 'workassignmentRedIcon');

      this.addSource(servicesCity);
      this.addSource(servicesProfit);
      this.addSource(servicesNonProfit);
      this.addSource(servicesCare);

      this.addLayer(environment.servicesCityLayerId, servicesCity, 'location_city', 'visible');
      this.addLayer(environment.servicesNonProfitLayerId, servicesNonProfit, 'sports_football');
      this.addLayer(environment.servicesProfitLayerId, servicesProfit, 'grocery_store');
      this.addLayer(environment.servicesCareLayerId, servicesCare, 'medical_services');

      this.selectedLayerId$ = this.store.pipe(select(getLayerId));
      this.selectedLayerId$.subscribe(
        id => {
          this.ChangeLayer(id, 'visible');
        }
      );

      this.map.on('moveend', () => {
        // @ts-ignore
        const features: Marker[] = this.map.queryRenderedFeatures({layers: this.layers});
      });

      this.map.on('mousemove', environment.servicesProfitLayerId, (e: any) => {
// Change the cursor style as a UI indicator.
        this.map.getCanvas().style.cursor = 'pointer';

// Populate the popup and set its coordinates based on the feature.
        if (!e.features) {
          return;
        }
        const feature = e.features[0];
        const geometry = feature.geometry as any;
        popup
          .setLngLat(geometry.coordinates)
          .setText(feature.properties.data.name)
          .addTo(this.map);
      });


      this.map.on('mouseleave', environment.servicesProfitLayerId, () => {
        this.map.getCanvas().style.cursor = '';
        popup.remove();
      });

      this.makeMarkersClickable(environment.servicesCityLayerId);
      this.makeMarkersClickable(environment.servicesCareLayerId);
      this.makeMarkersClickable(environment.servicesProfitLayerId);
      this.makeMarkersClickable(environment.servicesNonProfitLayerId);
    });
  }

  addImage(url: string, name: string): void {
    this.map.loadImage(
      url,
      (error: any, image: any) => {
        if (error) {
          throw error;
        }
        this.map.addImage(name, image as any);
      });
  }

  addSource(source: Source) {
    const url = 'mapbox://' + source.tileId;
    this.map.addSource(source.sourceId, {
      type: 'vector',
      url
    });
  }

  addLayer(layerId : string, source : Source, iconImage: string, visibility = 'none'): void {
    this.map.addLayer({
      id: layerId,
      source: source.sourceId,
      'source-layer': source.tileName,
      type: 'symbol',
      layout: this.setLayoutLayer(iconImage,visibility),
    })
  }

  private setLayoutLayer(iconImage: string, visibility: string) {
    return {
      'icon-image': iconImage,
      'icon-size': 0.6,
      'icon-allow-overlap': true,
      'visibility': visibility
    };
  }

  makeMarkersClickable(layerId: string): void
  {
    this.map.on('click', layerId, (e: any) => {
// Change the cursor style as a UI indicator.
      this.map.getCanvas().style.cursor = 'pointer';

      if (!e.features) {
        return;
      }
      const feature: Marker = e.features[0];
      this.onClickMarker(feature);
    });
  }

  private hideLayer(layerId: string) {
    this.map.setLayoutProperty(layerId, 'visibility', 'none');
  }
}


