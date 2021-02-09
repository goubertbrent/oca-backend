import { Injectable, NgZone } from '@angular/core';

export interface ResolvedAddress {
  streetNumber: string | null;
  street: string | null;
  locality: string | null;
  country: string | null;
  postalCode: string | null;
}

@Injectable({ providedIn: 'root' })
export class GoogleMapsApiService {
  constructor(private zone: NgZone) {
  }

  geocode(request: google.maps.GeocoderRequest): Promise<google.maps.GeocoderResult> {
    return new Promise((resolve, reject) => {
      new google.maps.Geocoder().geocode(request, (results, status) => {
        this.zone.run(() => {
          if (status === google.maps.GeocoderStatus.OK) {
            resolve(results[ 0 ]);
          } else {
            reject(status);
          }
        });
      });
    });
  }

  addressComponentsToObject(addressComponents: google.maps.GeocoderAddressComponent[]): ResolvedAddress {
    const result: ResolvedAddress = {
      streetNumber: null,
      street: null,
      locality: null,
      country: null,
      postalCode: null,
    };
    for (const component of addressComponents ?? []) {
      for (const type of component.types) {
        switch (type) {
          case 'street_number':
            result.streetNumber = component.long_name;
            break;
          case 'route':
            result.street = component.long_name;
            break;
          case 'locality':
            result.locality = component.long_name;
            break;
          case 'country':
            result.country = component.short_name;
            break;
          case 'postal_code':
            result.postalCode = component.long_name;
            break;
        }
      }
    }
    return result;
  }
}
