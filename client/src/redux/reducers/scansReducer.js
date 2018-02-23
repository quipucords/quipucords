import _ from 'lodash';
import helpers from '../../common/helpers';
import { scansTypes } from '../constants';

const initialState = {
  persist: {},

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: []
  },

  detail: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scan: {}
  },

  results: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    results: []
  },

  action: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    add: false,
    start: false,
    cancel: false,
    pause: false,
    restart: false
  }
};

const scansReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case scansTypes.GET_SCANS_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          pending: false,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCANS_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          scans: state.view.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCANS_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          scans: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCAN_REJECTED:
      return helpers.setStateProp(
        'detail',
        {
          pending: false,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCAN_PENDING:
      return helpers.setStateProp(
        'detail',
        {
          pending: true,
          scan: state.detail.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCAN_FULFILLED:
      return helpers.setStateProp(
        'detail',
        {
          scan: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCAN_RESULTS_REJECTED:
      return helpers.setStateProp(
        'results',
        {
          pending: false,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCAN_RESULTS_PENDING:
      return helpers.setStateProp(
        'results',
        {
          pending: true,
          results: state.results.results
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCAN_RESULTS_FULFILLED:
      return helpers.setStateProp(
        'results',
        {
          results: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.ADD_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          add: true,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.ADD_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.ADD_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.START_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          start: true,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.START_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.START_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.CANCEL_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          cancel: true,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.CANCEL_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.CANCEL_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.PAUSE_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          pause: true,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.PAUSE_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.PAUSE_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.RESTART_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          restart: true,
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.RESTART_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.RESTART_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: false,
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

export { initialState, scansReducer };

export default scansReducer;
