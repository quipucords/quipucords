import helpers from '../../common/helpers';
import { reportsTypes } from '../constants';

const initialState = {
  persist: {},

  deployments: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  },

  details: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  }
};

const reportsReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case helpers.rejectedAction(reportsTypes.GET_REPORT_DEPLOYMENTS):
    case helpers.rejectedAction(reportsTypes.GET_REPORT_DEPLOYMENTS_CSV):
      return helpers.setStateProp(
        'deployments',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    case helpers.rejectedAction(reportsTypes.GET_REPORT_DETAILS):
    case helpers.rejectedAction(reportsTypes.GET_REPORT_DETAILS_CSV):
      return helpers.setStateProp(
        'details',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(reportsTypes.GET_REPORT_DEPLOYMENTS):
    case helpers.pendingAction(reportsTypes.GET_REPORT_DEPLOYMENTS_CSV):
      return helpers.setStateProp(
        'deployments',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.pendingAction(reportsTypes.GET_REPORT_DETAILS):
    case helpers.pendingAction(reportsTypes.GET_REPORT_DETAILS_CSV):
      return helpers.setStateProp(
        'details',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(reportsTypes.GET_REPORT_DEPLOYMENTS):
      return helpers.setStateProp(
        'deployments',
        {
          reports: action.payload.data,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.fulfilledAction(reportsTypes.GET_REPORT_DETAILS):
      return helpers.setStateProp(
        'details',
        {
          reports: action.payload.data,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.fulfilledAction(reportsTypes.GET_REPORT_DEPLOYMENTS_CSV):
      return helpers.setStateProp(
        'deployments',
        {
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.fulfilledAction(reportsTypes.GET_REPORT_DETAILS_CSV):
      return helpers.setStateProp(
        'details',
        {
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    default:
      return state;
  }
};

export { initialState, reportsReducer };

export default reportsReducer;
