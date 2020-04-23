import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, resultOrEmptyArray, ResultState } from '../shared/call-state';
import {
  AppointmentExtendedDetails,
  AppointmentListItem,
  AppointmentsList,
  AvailableDays,
  AvailableTimes,
  BookGovAppointmentExtendedDetailsResponse,
  BookGovAppointmentResponse,
  Locations,
  Product,
  ProductDetails,
  SelectedProduct,
  SelectedProductsMapping,
} from './appointments';

export const JCC_APPOINTMENTS_FEATURE = 'jcc-appointments';

export interface JccAppointmentsState {
  appointments: ResultState<AppointmentsList>;
  products: ResultState<Product[]>;
  productDetails: { [ key: string ]: ProductDetails };
  selectableProducts: ResultState<Product[]>;
  selectedProducts: SelectedProductsMapping;
  locations: ResultState<Locations>;
  availableDays: ResultState<AvailableDays>;
  availableTimes: ResultState<AvailableTimes>;
  requiredFields: ResultState<(keyof AppointmentExtendedDetails)[]>;
  newAppointment: ResultState<BookGovAppointmentResponse | BookGovAppointmentExtendedDetailsResponse>
}

const getJccState = createFeatureSelector<JccAppointmentsState>(JCC_APPOINTMENTS_FEATURE);

export const initialJccAppointmentsState: JccAppointmentsState = {
  appointments: initialStateResult,
  products: initialStateResult,
  selectableProducts: initialStateResult,
  productDetails: {},
  selectedProducts: {},
  locations: initialStateResult,
  availableDays: initialStateResult,
  availableTimes: initialStateResult,
  requiredFields: initialStateResult,
  newAppointment: initialStateResult,
};

export const getAppointments = createSelector(getJccState, s => {
  const resultArray: AppointmentListItem[] = [];
  if (s.appointments.state === CallStateType.SUCCESS) {
    for (const appointment of s.appointments.result.appointments) {
      const location = s.appointments.result.locations[ appointment.locationID ];
      const productIds = appointment.productID.split(',');
      const uniqueProducts = new Set(productIds);
      const productCounts: { [ key: string ]: number } = {};
      for (const productId of productIds) {
        if (productId in productCounts) {
          productCounts[ productId ] += 1;
        } else {
          productCounts[ productId ] = 1;
        }
      }
      const products: SelectedProduct[] = [];
      for (const productId of uniqueProducts) {
        products.push({
          id: productId,
          amount: productCounts[ productId ],
          productDetails: s.appointments.result.products[ productId ],
        });
      }
      resultArray.push({
        appointment,
        location,
        products,
      });
    }
  }
  return resultArray;
});
export const isLoadingAppointments = createSelector(getJccState, s => s.appointments.state === CallStateType.LOADING);
export const hasNoAppointments = createSelector(getJccState, s => s.appointments.state === CallStateType.SUCCESS && s.appointments.result.appointments.length === 0);
export const getProductsList = createSelector(getJccState, s => resultOrEmptyArray(s.products));
export const getProductsMapping = createSelector(getProductsList, products => products.reduce((result, product) => {
  result[ product.productId ] = product;
  return result;
}, {} as { [ key: string ]: Product }));
export const getProductDetails = createSelector(getJccState, (s: JccAppointmentsState) => s.productDetails);
export const getSelectedProducts = createSelector(getJccState, s => s.selectedProducts);
export const getSelectedProductsIds = createSelector(getSelectedProducts, selectedProducts => {
  const ids = [];
  for (const productId of Object.keys(selectedProducts)) {
    const count = selectedProducts[ productId ];
    for (let i = 0; i < count; i++) {
      ids.push(productId);
    }
  }
  return ids;
});
export const getSelectableProducts = createSelector(getJccState, getSelectedProductsIds, (s, productIds) => {
  return resultOrEmptyArray(s.selectableProducts).filter(product => !productIds.includes(product.productId));
});
export const getSelectedProductsList = createSelector(getJccState, getProductDetails, (s, productsDetails) => {
  return Object.keys(s.selectedProducts).map(productId => ({
    id: productId,
    productDetails: productsDetails[ productId ],
    amount: s.selectedProducts[ productId ],
  }));
});
export const isProductsLoading = createSelector(getJccState, state => {
  return state.products.state === CallStateType.LOADING
    || state.selectableProducts.state === CallStateType.LOADING
    || state.locations.state === CallStateType.LOADING;
});
export const getLocations = createSelector(getJccState, s => resultOrEmptyArray(s.locations));
export const getAvailableDays = createSelector(getJccState, s => resultOrEmptyArray(s.availableDays));
export const getAvailableTimes = createSelector(getJccState, s => resultOrEmptyArray(s.availableTimes));
export const getRequiredFields = createSelector(getJccState, s => resultOrEmptyArray(s.requiredFields));
export const isCreatingAppointment = createSelector(getJccState, s => s.newAppointment.state === CallStateType.LOADING);
