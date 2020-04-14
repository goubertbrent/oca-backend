import { CallStateType, stateError, stateLoading, stateSuccess } from '../shared/call-state';
import { JccAppointmentsActions, JccAppointmentsActionTypes } from './jcc-appointments-actions';
import { initialJccAppointmentsState, JccAppointmentsState } from './jcc-appointments.state';

export function jccAppointmentsReducer(state = initialJccAppointmentsState, action: JccAppointmentsActions): JccAppointmentsState {
  switch (action.type) {
    case JccAppointmentsActionTypes.GET_APPOINTMENTS:
      return { ...state, appointments: stateLoading(initialJccAppointmentsState.appointments.result) };
    case JccAppointmentsActionTypes.GET_APPOINTMENTS_SUCCESS:
      return { ...state, appointments: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_APPOINTMENTS_FAILED:
      return { ...state, appointments: stateError(action.error, state.appointments.result) };
    case JccAppointmentsActionTypes.CANCEL_APPOINTMENT_SUCCESS:
      return {
        ...state,
        appointments: state.appointments.state === CallStateType.SUCCESS ? {
          ...state.appointments,
          result: {
            ...state.appointments.result,
            appointments: state.appointments.result.appointments.filter(a => a.id !== action.payload.appointmentID),
          },
        } : state.appointments,
      };
    case JccAppointmentsActionTypes.GET_PRODUCTS:
      return {
        ...state,
        products: stateLoading(initialJccAppointmentsState.products.result),
        selectedProducts: initialJccAppointmentsState.selectedProducts,
        selectableProducts: initialJccAppointmentsState.selectableProducts,
        availableDays: initialJccAppointmentsState.availableDays,
        availableTimes: initialJccAppointmentsState.availableTimes,
        requiredFields: initialJccAppointmentsState.requiredFields,
        locations: initialJccAppointmentsState.locations,
      };
    case JccAppointmentsActionTypes.GET_PRODUCTS_SUCCESS:
      return {
        ...state,
        products: stateSuccess(action.payload),
        selectableProducts: stateSuccess(action.payload),
      };
    case JccAppointmentsActionTypes.GET_PRODUCTS_FAILED:
      return { ...state, products: stateError(action.error, state.products.result) };
    case JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS:
      return { ...state, selectableProducts: stateLoading(state.selectableProducts.result) };
    case JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS_SUCCESS:
      return { ...state, selectableProducts: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS_FAILED:
      return { ...state, selectableProducts: stateError(action.error, state.selectableProducts.result) };
    case JccAppointmentsActionTypes.GET_PRODUCT_DETAILS_COMPLETE:
      return { ...state, productDetails: { ...state.productDetails, [ action.payload.productId ]: action.payload.product } };
    case JccAppointmentsActionTypes.ADD_PRODUCT:
      return { ...state, selectedProducts: { ...state.selectedProducts, [ action.payload.product.productId ]: 1 } };
    case JccAppointmentsActionTypes.UPDATE_PRODUCT:
      return { ...state, selectedProducts: { ...state.selectedProducts, [ action.payload.productId ]: action.payload.amount } };
    case JccAppointmentsActionTypes.DELETE_PRODUCT:
      const { [ action.payload.productId ]: _, ...newSelectedProducts } = state.selectedProducts;
      return {
        ...state,
        selectedProducts: newSelectedProducts,
        // Reset locations
        locations: initialJccAppointmentsState.locations,
        // no products selected -> reset selectable products to all products
        selectableProducts: Object.keys(newSelectedProducts).length === 0 ? state.products : state.selectableProducts,
      };
    case JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS:
      return { ...state, locations: stateLoading(initialJccAppointmentsState.locations.result) };
    case JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS_SUCCESS:
      return { ...state, locations: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS_FAILED:
      return { ...state, locations: stateError(action.error, state.locations.result) };
    case JccAppointmentsActionTypes.GET_AVAILABLE_DAYS:
      return { ...state, availableDays: stateLoading(initialJccAppointmentsState.availableDays.result) };
    case JccAppointmentsActionTypes.GET_AVAILABLE_DAYS_SUCCESS:
      return { ...state, availableDays: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_AVAILABLE_DAYS_FAILED:
      return { ...state, availableDays: stateError(action.error, state.availableDays.result) };
    case JccAppointmentsActionTypes.GET_TIMES_FOR_DAY:
      return { ...state, availableTimes: stateLoading(initialJccAppointmentsState.availableTimes.result) };
    case JccAppointmentsActionTypes.GET_TIMES_FOR_DAY_SUCCESS:
      return { ...state, availableTimes: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_TIMES_FOR_DAY_FAILED:
      return { ...state, availableTimes: stateError(action.error, state.availableTimes.result) };
    case JccAppointmentsActionTypes.GET_REQUIRED_FIELDS:
      return { ...state, requiredFields: stateLoading(state.requiredFields.result) };
    case JccAppointmentsActionTypes.GET_REQUIRED_FIELDS_SUCCESS:
      return { ...state, requiredFields: stateSuccess(action.payload) };
    case JccAppointmentsActionTypes.GET_REQUIRED_FIELDS_FAILED:
      return { ...state, requiredFields: stateError(action.error, state.requiredFields.result) };
  }
  return state;
}
