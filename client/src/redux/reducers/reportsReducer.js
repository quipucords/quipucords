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
    case helpers.rejectedAction(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, {
        error: action.error,
        errorMessage: helpers.getErrorMessageFromResults(action.payload)
      });

    // Loading/Pending
    case helpers.pendingAction(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, { pending: true });

    // Success/Fulfilled
    case helpers.fulfilledAction(reportsTypes.GET_REPORT):
      return Object.assign({}, initialState, { reports: action.payload.data, fulfilled: true });

    default:
      return state;
  }
};

export { initialState, reportsReducer };

export default reportsReducer;
