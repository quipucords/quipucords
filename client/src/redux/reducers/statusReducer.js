import { statusTypes } from '../constants';
import helpers from '../../common/helpers';

const initialState = {
  error: false,
  errorMessage: '',
  pending: false,
  fulfilled: false,
  currentStatus: {}
};

const statusReducer = (state = initialState, action) => {
  switch (action.type) {
    // Error/Rejected
    case helpers.REJECTED_ACTION(statusTypes.STATUS_INFO):
      return Object.assign({}, initialState, {
        error: action.error,
        errorMessage: helpers.getErrorMessageFromResults(action.payload)
      });

    // Loading/Pending
    case helpers.PENDING_ACTION(statusTypes.STATUS_INFO):
      return Object.assign({}, initialState, {
        pending: true
      });

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(statusTypes.STATUS_INFO):
      return Object.assign({}, initialState, {
        currentStatus: action.payload.data,
        fulfilled: true
      });

    default:
      return state;
  }
};

statusReducer.initialState = initialState;

export { statusReducer as default, initialState, statusReducer };
