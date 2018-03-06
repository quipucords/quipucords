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
    case reportsTypes.GET_REPORT_DEPLOYMENTS_REJECTED:
    case reportsTypes.GET_REPORT_DEPLOYMENTS_CSV_REJECTED:
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

    case reportsTypes.GET_REPORT_DETAILS_REJECTED:
    case reportsTypes.GET_REPORT_DETAILS_CSV_REJECTED:
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
    case reportsTypes.GET_REPORT_DEPLOYMENTS_PENDING:
    case reportsTypes.GET_REPORT_DEPLOYMENTS_CSV_PENDING:
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

    case reportsTypes.GET_REPORT_DETAILS_PENDING:
    case reportsTypes.GET_REPORT_DETAILS_CSV_PENDING:
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
    case reportsTypes.GET_REPORT_DEPLOYMENTS_FULFILLED:
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

    case reportsTypes.GET_REPORT_DETAILS_FULFILLED:
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

    case reportsTypes.GET_REPORT_DEPLOYMENTS_CSV_FULFILLED:
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

    case reportsTypes.GET_REPORT_DETAILS_CSV_FULFILLED:
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
