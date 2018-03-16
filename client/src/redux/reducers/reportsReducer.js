import helpers from '../../common/helpers';
import { reportsTypes } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  pending: false,
  fulfilled: false,
  reports: []
};

const reportsReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case helpers.REJECTED_ACTION(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, {
        error: action.error,
        errorMessage: helpers.getErrorMessageFromResults(action.payload)
      });

    // Loading/Pending
    case helpers.PENDING_ACTION(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, { pending: true });

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, { reports: action.payload.data, fulfilled: true });

    default:
      return state;
  }
};

export { initialState, reportsReducer };

export default reportsReducer;
