import { statusTypes } from '../constants';
import helpers from '../../common/helpers';

const initialState = {
  error: false,
  errorMessage: '',
  pending: false,
  fulfilled: false,
  currentStatus: {}
};

export default function statusReducer(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case statusTypes.STATUS_INFO_REJECTED:
      return Object.assign({}, initialState, {
        error: action.error,
        errorMessage: helpers.getErrorMessageFromResults(action.payload)
      });

    // Loading/Pending
    case statusTypes.STATUS_INFO_PENDING:
      return Object.assign({}, initialState, {
        pending: true
      });

    // Success/Fulfilled
    case statusTypes.STATUS_INFO_FULFILLED:
      return Object.assign({}, initialState, {
        currentStatus: action.payload.data,
        fulfilled: true
      });

    default:
      return state;
  }
}
